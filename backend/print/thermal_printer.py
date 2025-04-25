import os
import tempfile
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import cairosvg
import win32print
import win32ui
from escpos.printer import File


class ThermalPrinter:
    """
    A class to handle printing to a thermal printer.
    This module supports printing numbers, timestamps, and SVG logos.
    """

    def __init__(self, printer_name=None, logo_path=None, font_size=48, time_font_size=22,
                 paper_width_mm=80, dpi=203):
        """
        Initialize the thermal printer.

        Args:
            printer_name (str): Name of the printer. If None, uses default printer.
            logo_path (str): Path to the SVG logo file.
            font_size (int): Font size for the number.
            time_font_size (int): Font size for the timestamp.
            paper_width_mm (int): Paper width in millimeters (typically 58mm or 80mm).
            dpi (int): Dots per inch (typically 203 DPI for thermal printers).
        """
        self.printer_name = printer_name if printer_name else win32print.GetDefaultPrinter()
        self.logo_path = 'Mediamodifier-Design.svg'
        self.font_size = font_size
        self.time_font_size = time_font_size

        # Convert paper width from mm to pixels at the given DPI
        # 1 inch = 25.4 mm
        self.paper_width_pixels = int((paper_width_mm / 25.4) * dpi)

        # Try to locate a suitable font
        try:
            # Try to find a common font that should be available on most systems
            self.font = ImageFont.truetype("arial.ttf", self.font_size)
            self.time_font = ImageFont.truetype("arial.ttf", self.time_font_size)
        except IOError:
            # Fallback to default font
            self.font = ImageFont.load_default()
            self.time_font = ImageFont.load_default()

    def _convert_svg_to_png(self, width=None):
        """
        Convert the SVG logo to PNG format.

        Args:
            width (int): Desired width of the PNG.

        Returns:
            str: Path to the temporary PNG file.
        """
        if not self.logo_path or not os.path.exists(self.logo_path):
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
        if time is None:
            time = datetime.now()

        time_str = time.strftime("%Y-%m-%d %H:%M:%S")

        # Create a blank image
        img = Image.new('L', (self.paper_width_pixels, 350), 255)  # 'L' mode = 8-bit pixels, black and white
        draw = ImageDraw.Draw(img)

        # Calculate vertical positions
        current_y = 10

        # Add logo if available
        if self.logo_path and os.path.exists(self.logo_path):
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

        # Print using Windows printer API
        self._print_image_to_printer(temp_file.name)

        # Clean up
        os.unlink(temp_file.name)

    def _print_image_to_printer(self, image_path):
        """
        Print an image to the Windows printer.

        Args:
            image_path (str): Path to the image file.
        """
        try:
            # Method 1: Using Windows API
            hprinter = win32print.OpenPrinter(self.printer_name)
            try:
                hdc = win32ui.CreateDC()
                hdc.CreatePrinterDC(self.printer_name)

                # Start the print job
                hdc.StartDoc(image_path)
                hdc.StartPage()

                # Load and print the image
                img = Image.open(image_path)
                dib = ImageWin.Dib(img)
                dib.draw(hdc.GetHandleOutput(), (0, 0, img.width, img.height))

                # End the print job
                hdc.EndPage()
                hdc.EndDoc()
                hdc.DeleteDC()
            finally:
                win32print.ClosePrinter(hprinter)
        except Exception as e:
            print(f"Error printing with Windows API: {e}")

            # Fallback method: Try using ESC/POS library
            try:
                printer = File(self.printer_name)
                printer.image(image_path)
                printer.cut()
            except Exception as e2:
                print(f"Error printing with ESC/POS: {e2}")
                # If both methods fail, try direct printing
                raw_data = open(image_path, 'rb').read()
                printer_handle = win32print.OpenPrinter(self.printer_name)
                try:
                    job = win32print.StartDocPrinter(printer_handle, 1, ("Print Job", None, "RAW"))
                    try:
                        win32print.StartPagePrinter(printer_handle)
                        win32print.WritePrinter(printer_handle, raw_data)
                        win32print.EndPagePrinter(printer_handle)
                    finally:
                        win32print.EndDocPrinter(printer_handle)
                finally:
                    win32print.ClosePrinter(printer_handle)


# Import fix for ImageWin on Windows
try:
    from PIL import ImageWin
except ImportError:
    # If ImageWin is not available, define a fallback
    class ImageWin:
        class Dib:
            def __init__(self, image):
                self.image = image

            def draw(self, hdc, dst):
                # This is a placeholder - won't actually work without ImageWin
                pass

# Example usage
if __name__ == "__main__":
    # Example with a sample SVG logo
    SAMPLE_SVG = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
    <svg xmlns="http://www.w3.org/2000/svg" width="100" height="50" viewBox="0 0 100 50">
      <rect width="100" height="50" fill="white"/>
      <text x="50" y="30" font-family="Arial" font-size="20" text-anchor="middle" fill="black">LOGO</text>
    </svg>
    """

    # Save sample SVG to a temporary file
    with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as temp_svg:
        temp_svg.write(SAMPLE_SVG.encode('utf-8'))

    # Create printer and print
    printer = ThermalPrinter(logo_path=temp_svg.name)
    printer.print(12345, datetime.now())

    # Clean up
    os.unlink(temp_svg.name)