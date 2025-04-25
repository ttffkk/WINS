import os
import tempfile
from datetime import datetime
import subprocess
from PIL import Image, ImageDraw, ImageFont
import cairosvg
import cups


class ThermalPrinter:
    """
    A class to handle printing to a CAPD245 thermal printer on Linux/Debian.
    This module supports printing numbers, timestamps, and a fixed SVG logo.
    """

    def __init__(self, font_size=48, time_font_size=22, paper_width_mm=80, dpi=203):
        """
        Initialize the thermal printer.

        Args:
            font_size (int): Font size for the number.
            time_font_size (int): Font size for the timestamp.
            paper_width_mm (int): Paper width in millimeters (typically 58mm or 80mm for CAPD245).
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

        # Find the printer
        self.detect_printer()

    def detect_printer(self):
        """
        Detect the CAPD245 printer.
        This will try multiple methods to identify the printer.
        """
        self.printer_found = False

        # Method 1: Try to find using CUPS
        try:
            conn = cups.Connection()
            printers = conn.getPrinters()

            # Look specifically for CAPD245 or similar names
            for printer_name in printers:
                if "CAPD" in printer_name.upper() or "245" in printer_name:
                    self.cups_printer_name = printer_name
                    print(f"Found CAPD245 printer via CUPS: {self.cups_printer_name}")
                    self.cups_conn = conn
                    self.printer_found = True
                    self.print_method = "cups"
                    return

            # If no specific CAPD245 found, use the first available printer
            if printers:
                self.cups_printer_name = list(printers.keys())[0]
                print(f"Using default printer via CUPS: {self.cups_printer_name}")
                self.cups_conn = conn
                self.printer_found = True
                self.print_method = "cups"
                return
        except Exception as e:
            print(f"CUPS detection failed: {e}")

        # Method 2: Check for device files commonly used by thermal printers
        try:
            # Common device paths for printers including serial ports
            device_paths = [
                "/dev/usb/lp0",  # USB printer
                "/dev/usb/lp1",
                "/dev/lp0",  # Parallel port printer
                "/dev/lp1",
                "/dev/ttyS0",  # Serial port (COM1 in Windows)
                "/dev/ttyS1",  # Serial port (COM2 in Windows)
                "/dev/ttyUSB0",  # USB-to-Serial adapter
                "/dev/ttyUSB1"
            ]

            for path in device_paths:
                if os.path.exists(path):
                    print(f"Found potential printer device: {path}")
                    self.device_path = path
                    self.printer_found = True
                    self.print_method = "device"
                    return
        except Exception as e:
            print(f"Device file detection failed: {e}")

        print("Warning: No printer was automatically detected")
        print("Setting up for manual/fallback printing methods")
        self.print_method = "fallback"
        self.printer_found = True  # We'll attempt to print anyway

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
        success = False
        error_messages = []

        # Try the primary detected method first
        try:
            if self.print_method == "cups":
                self._print_with_cups(temp_file.name)
                success = True
            elif self.print_method == "device":
                self._print_to_device(temp_file.name)
                success = True
            else:
                # Will try fallback methods below
                pass
        except Exception as e:
            error_messages.append(f"Primary printing method failed: {e}")

        # If primary method failed or we're in fallback mode, try alternatives
        if not success:
            print("Trying alternative printing methods...")
            try:
                success = self._try_alternative_printing_methods(temp_file.name)
            except Exception as e:
                error_messages.append(f"Alternative printing methods failed: {e}")

        # Clean up
        os.unlink(temp_file.name)

        # Report final status
        if not success:
            print("All printing methods failed with the following errors:")
            for msg in error_messages:
                print(f"- {msg}")
            print("\nPlease check your printer connection and try the following:")
            print("1. Make sure the printer is powered on")
            print("2. Check if the printer is configured in CUPS (http://localhost:631)")
            print("3. Try printing a test page from the system")

    def _print_with_cups(self, image_path):
        """Print using CUPS."""
        job_id = self.cups_conn.printFile(
            self.cups_printer_name,
            image_path,
            "Thermal Print Job",
            {}
        )
        print(f"Print job submitted with ID: {job_id}")

    def _print_to_device(self, image_path):
        """Print directly to device file."""
        try:
            # For direct device printing, convert image to ESC/POS commands
            # First, see if python-escpos can handle it
            try:
                from escpos.printer import File
                printer = File(self.device_path)
                img = Image.open(image_path)
                printer.image(img)
                printer.cut()
                print(f"Printed to {self.device_path} using ESC/POS commands")
                return
            except (ImportError, Exception) as e:
                print(f"ESC/POS printing failed: {e}")

            # If the above fails, try direct writing to device
            with open(image_path, 'rb') as f:
                data = f.read()

            with open(self.device_path, 'wb') as p:
                # Add printer initialization sequence for CAPD245 (ESC @)
                p.write(b'\x1b\x40')  # ESC @ - Initialize printer

                # Write raw data (not ideal, but a fallback)
                p.write(data)

                # Add paper cut command (if supported by printer)
                p.write(b'\x1d\x56\x41\x03')  # GS V A - Paper cut

            print(f"Printed raw data to {self.device_path}")
        except Exception as e:
            print(f"Direct device printing failed: {e}")
            raise

    def _try_alternative_printing_methods(self, image_path):
        """Try alternative printing methods if the primary method fails."""
        methods = ["lp", "lpr", "system_print_command", "raw_devices"]

        for method in methods:
            try:
                if method == "lp":
                    # Try using lp command
                    subprocess.run(["lp", image_path], check=True)
                    print("Successfully printed using lp command")
                    return True

                elif method == "lpr":
                    # Try using lpr command
                    subprocess.run(["lpr", image_path], check=True)
                    print("Successfully printed using lpr command")
                    return True

                elif method == "system_print_command":
                    # Try various system print commands
                    # For CAPD245, there might be a specific utility
                    commands = [
                        ["capd-print", image_path],  # Hypothetical CAPD utility
                        ["python3", "-m", "escpos.cli", "-p", "file:/dev/usb/lp0", "image", image_path]
                    ]

                    for cmd in commands:
                        try:
                            subprocess.run(cmd, check=True)
                            print(f"Successfully printed using command: {' '.join(cmd)}")
                            return True
                        except (subprocess.SubprocessError, FileNotFoundError):
                            pass

                elif method == "raw_devices":
                    # Try writing directly to various device files
                    device_paths = [
                        "/dev/usb/lp0", "/dev/usb/lp1",
                        "/dev/lp0", "/dev/lp1",
                        "/dev/ttyS0", "/dev/ttyS1",
                        "/dev/ttyUSB0", "/dev/ttyUSB1"
                    ]

                    for path in device_paths:
                        if os.path.exists(path):
                            try:
                                # Try direct writing
                                with open(image_path, 'rb') as f:
                                    data = f.read()
                                with open(path, 'wb') as p:
                                    # Add printer initialization and cut commands
                                    p.write(b'\x1b\x40')  # Initialize
                                    p.write(data)
                                    p.write(b'\x1d\x56\x00')  # Cut paper
                                print(f"Successfully printed using raw write to {path}")
                                return True
                            except:
                                pass
            except Exception as e:
                print(f"Alternative method {method} failed: {e}")

        return False


# Example usage
if __name__ == "__main__":
    # Create printer instance
    printer = ThermalPrinter()

    # Print a number with the current time
    printer.print(12345)

    # Or with a specific timestamp
    # printer.print(67890, datetime.datetime(2025, 4, 25, 14, 30, 0))