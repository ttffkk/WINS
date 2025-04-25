import os
import tempfile
from datetime import datetime
import subprocess
from PIL import Image, ImageDraw, ImageFont
import cairosvg
import cups
from escpos.printer import Usb


class ThermalPrinter:
    """
    A class to handle printing to a USB thermal printer on Linux/Debian.
    This module supports printing numbers, timestamps, and a fixed SVG logo.
    """

    def __init__(self, font_size=48, time_font_size=22, paper_width_mm=80, dpi=203):
        """
        Initialize the thermal printer.

        Args:
            font_size (int): Font size for the number.
            time_font_size (int): Font size for the timestamp.
            paper_width_mm (int): Paper width in millimeters (typically 58mm or 80mm).
            dpi (int): Dots per inch (typically 203 DPI for thermal printers).
        """
        self.font_size = font_size
        self.time_font_size = time_font_size

        # Convert paper width from mm to pixels at the given DPI
        # 1 inch = 25.4 mm
        self.paper_width_pixels = int((paper_width_mm / 25.4) * dpi)

        # Get the script directory for the SVG file
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.logo_path = os.path.join(self.script_dir, "Mediamodifier-Design.svg")

        # Check if the logo exists
        if not os.path.exists(self.logo_path):
            print(f"Warning: Logo file not found at {self.logo_path}")

        # Try to locate a suitable font
        try:
            # Common fonts on Debian/Linux
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
                "/usr/share/fonts/truetype/ttf-bitstream-vera/Vera.ttf"
            ]

            # Try each font until one works
            for font_path in font_paths:
                if os.path.exists(font_path):
                    self.font = ImageFont.truetype(font_path, self.font_size)
                    self.time_font = ImageFont.truetype(font_path, self.time_font_size)
                    break
            else:
                # Fallback to default font if none of the above exist
                self.font = ImageFont.load_default()
                self.time_font = ImageFont.load_default()
        except IOError:
            # Fallback to default font
            self.font = ImageFont.load_default()
            self.time_font = ImageFont.load_default()

        # Find the USB printer
        self.detect_usb_printer()

    def detect_usb_printer(self):
        """
        Detect the connected USB thermal printer.
        This will try multiple methods to identify the printer.
        """
        self.printer_found = False

        # Method 1: Try to find using CUPS
        try:
            conn = cups.Connection()
            printers = conn.getPrinters()
            if printers:
                self.cups_printer_name = list(printers.keys())[0]
                print(f"Found printer via CUPS: {self.cups_printer_name}")
                self.cups_conn = conn
                self.printer_found = True
                self.print_method = "cups"
                return
        except Exception as e:
            print(f"CUPS detection failed: {e}")

        # Method 2: Try to find the USB device automatically
        try:
            # Get list of USB devices using lsusb
            lsusb_output = subprocess.check_output(["lsusb"], universal_newlines=True)
            lines = lsusb_output.strip().split('\n')

            # Look for printer-related devices
            printer_keywords = ["print", "epson", "star", "thermal", "receipt", "pos"]

            for line in lines:
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in printer_keywords):
                    # Extract vendor and product ID
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "ID":
                            id_part = parts[i + 1]
                            vendor_id, product_id = id_part.split(':')

                            # Convert to integers
                            self.vendor_id = int(vendor_id, 16)
                            self.product_id = int(product_id, 16)

                            print(f"Found USB printer: Vendor ID 0x{vendor_id}, Product ID 0x{product_id}")
                            self.printer_found = True
                            self.print_method = "usb"
                            return

            # If no printer-specific device was found, try the first USB device
            if lines:
                for line in lines:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "ID":
                            id_part = parts[i + 1]
                            vendor_id, product_id = id_part.split(':')

                            # Convert to integers
                            self.vendor_id = int(vendor_id, 16)
                            self.product_id = int(product_id, 16)

                            print(f"Using first USB device: Vendor ID 0x{vendor_id}, Product ID 0x{product_id}")
                            self.printer_found = True
                            self.print_method = "usb"
                            return

        except Exception as e:
            print(f"USB auto-detection failed: {e}")

        # Method 3: Check for device files
        try:
            # Check common device files for printers
            device_paths = [
                "/dev/usb/lp0",
                "/dev/usb/lp1",
                "/dev/lp0",
                "/dev/lp1"
            ]

            for path in device_paths:
                if os.path.exists(path):
                    print(f"Found printer device file: {path}")
                    self.device_path = path
                    self.printer_found = True
                    self.print_method = "file"
                    return
        except Exception as e:
            print(f"Device file detection failed: {e}")

        print("Warning: No printer was automatically detected")

    def _convert_svg_to_png(self, width=None):
        """
        Convert the SVG logo to PNG format.

        Args:
            width (int): Desired width of the PNG.

        Returns:
            str: Path to the temporary PNG file.
        """
        if not os.path.exists(self.logo_path):
            return None

        # Create a temporary file for the PNG
        temp_png = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        temp_png.close()

        # Convert SVG to PNG
        output_width = width if width else self.paper_width_pixels - 20  # Margin of 10px on each side
        cairosvg.svg2png(url=self.logo_path, write_to=temp_png.name, output_width=output_width)

        return temp_png.name

    def print(self, number, time=None):
        """
        Print the number, time, and logo on the thermal printer.

        Args:
            number (int): The number to print.
            time (datetime): The timestamp to print. If None, uses current time.
        """
        if not self.printer_found:
            print("Error: No printer was detected. Cannot print.")
            return

        if time is None:
            time = datetime.now()

        time_str = time.strftime("%Y-%m-%d %H:%M:%S")

        # Create a blank image
        img = Image.new('L', (self.paper_width_pixels, 350), 255)  # 'L' mode = 8-bit pixels, black and white
        draw = ImageDraw.Draw(img)

        # Calculate vertical positions
        current_y = 10

        # Add logo if available
        if os.path.exists(self.logo_path):
            logo_png_path = self._convert_svg_to_png()
            if logo_png_path:
                try:
                    logo_img = Image.open(logo_png_path)
                    # Center the logo
                    logo_x = (self.paper_width_pixels - logo_img.width) // 2
                    img.paste(logo_img, (logo_x, current_y))
                    current_y += logo_img.height + 20  # Add some spacing
                    # Clean up temporary file
                    os.unlink(logo_png_path)
                except Exception as e:
                    print(f"Error loading logo: {e}")

        # Add number (centered)
        number_str = str(number)
        number_width = draw.textlength(number_str, self.font)
        number_x = (self.paper_width_pixels - number_width) // 2
        draw.text((number_x, current_y), number_str, font=self.font, fill=0)

        # Calculate height of the text (approximate)
        current_y += self.font_size + 10

        # Add timestamp (centered)
        time_width = draw.textlength(time_str, self.time_font)
        time_x = (self.paper_width_pixels - time_width) // 2
        draw.text((time_x, current_y), time_str, font=self.time_font, fill=0)

        # Crop the image to remove unused space
        current_y += self.time_font_size + 30  # Add some spacing at the bottom
        img = img.crop((0, 0, self.paper_width_pixels, current_y))

        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        img.save(temp_file.name)
        temp_file.close()

        # Print using the appropriate method
        try:
            if self.print_method == "cups":
                self._print_with_cups(temp_file.name)
            elif self.print_method == "usb":
                self._print_with_usb(temp_file.name)
            elif self.print_method == "file":
                self._print_with_file(temp_file.name)
        except Exception as e:
            print(f"Error printing: {e}")
            print("Trying alternative printing methods...")
            self._try_alternative_printing_methods(temp_file.name)

        # Clean up
        os.unlink(temp_file.name)

    def _print_with_cups(self, image_path):
        """Print using CUPS."""
        job_id = self.cups_conn.printFile(
            self.cups_printer_name,
            image_path,
            "Thermal Print Job",
            {}
        )
        print(f"Print job submitted with ID: {job_id}")

    def _print_with_usb(self, image_path):
        """Print directly to USB device."""
        try:
            printer = Usb(self.vendor_id, self.product_id)
            img = Image.open(image_path)
            printer.image(img)
            printer.cut()
        except Exception as e:
            print(f"USB printing failed: {e}")
            raise

    def _print_with_file(self, image_path):
        """Print to device file."""
        try:
            from escpos.printer import File
            printer = File(self.device_path)
            img = Image.open(image_path)
            printer.image(img)
            printer.cut()
        except Exception as e:
            print(f"File printing failed: {e}")

            # Try raw printing as fallback
            try:
                with open(image_path, 'rb') as f:
                    data = f.read()
                with open(self.device_path, 'wb') as p:
                    p.write(data)
                print("Raw printing successful")
            except Exception as e2:
                print(f"Raw printing failed: {e2}")
                raise

    def _try_alternative_printing_methods(self, image_path):
        """Try alternative printing methods if the primary method fails."""
        methods = ["lp", "lpr", "raw"]

        for method in methods:
            try:
                if method == "lp":
                    # Try using lp command
                    subprocess.run(["lp", image_path], check=True)
                    print("Successfully printed using lp command")
                    return
                elif method == "lpr":
                    # Try using lpr command
                    subprocess.run(["lpr", image_path], check=True)
                    print("Successfully printed using lpr command")
                    return
                elif method == "raw":
                    # Try to find any printer device and write directly
                    device_paths = ["/dev/usb/lp0", "/dev/usb/lp1", "/dev/lp0", "/dev/lp1"]
                    for path in device_paths:
                        if os.path.exists(path):
                            with open(image_path, 'rb') as f:
                                data = f.read()
                            with open(path, 'wb') as p:
                                p.write(data)
                            print(f"Successfully printed using raw method to {path}")
                            return
            except Exception as e:
                print(f"Alternative method {method} failed: {e}")

        print("All printing methods failed. Please check your printer connection.")


# Example usage
if __name__ == "__main__":
    # Create printer instance
    printer = ThermalPrinter()

    # Print a number with the current time
    printer.print(12345)

    # Or with a specific timestamp
    # printer.print(67890, datetime.datetime(2025, 4, 25, 14, 30, 0))