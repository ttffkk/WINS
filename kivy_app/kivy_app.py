from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='kivy_app.log'
)
logger = logging.getLogger('TicketingApp')


class BackgroundLabel(Label):
    def __init__(self, bg_color=(1, 1, 1, 1), **kwargs):
        super(BackgroundLabel, self).__init__(**kwargs)
        self.bg_color = bg_color
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            Rectangle(pos=self.pos, size=self.size)


class TicketingSystem(BoxLayout):
    def __init__(self, **kwargs):
        super(TicketingSystem, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 20

        # Top "Now Serving" label (20% of height)
        self.serving_label = Label(
            text="Now Serving:",
            font_size=36,
            size_hint=(1, 0.1)
        )

        # Number display with white background (expanded to 70% of height)
        self.current_number = BackgroundLabel(
            bg_color=(1, 1, 1, 1),  # White background
            text="---",
            font_size=100,  # Increased font size for larger display
            bold=True,
            color=(0, 0, 0, 1),  # Black text for better contrast on white
            size_hint=(1, 0.7)
        )

        # Button container to center the button (20% of height)
        self.button_container = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.2)
        )

        # Spacer (left)
        self.button_container.add_widget(BoxLayout(size_hint=(0.25, 1)))

        # New ticket button - half width and centered
        self.ticket_button = Button(
            text="Request New Ticket",
            font_size=36,
            size_hint=(0.5, 1),
            background_color=(0.07, 0.25, 0.45, 1)  # Dark blue color like in your screenshot
        )
        self.ticket_button.bind(on_press=self.request_new_ticket)
        self.button_container.add_widget(self.ticket_button)

        # Spacer (right)
        self.button_container.add_widget(BoxLayout(size_hint=(0.25, 1)))

        # Add widgets to main layout
        self.add_widget(self.serving_label)
        self.add_widget(self.current_number)
        self.add_widget(self.button_container)

        # Start the polling for current number
        # Call every 5 seconds
        Clock.schedule_interval(self.update_current_number, 1)

        # FastAPI backend URL - adjust to your setup
        self.api_url = "http://localhost:8000"

    def request_new_ticket(self, instance):
        """Request a new ticket when button is pressed"""
        try:
            logger.info("Requesting new ticket")
            response = requests.post(f"{self.api_url}/new_ticket")

            if response.status_code == 200:
                ticket_data = response.json()
                ticket_number = ticket_data.get("ticket_number")
                logger.info(f"New ticket created: {ticket_number}")

                # Show confirmation feedback to the user
                self.ticket_button.text = f"Ticket #{ticket_number} Created"

                # Reset button text after 3 seconds
                Clock.schedule_once(self.reset_button_text, 3)
            else:
                logger.error(f"Failed to create ticket: {response.status_code}")
                self.ticket_button.text = "Error: Try Again"
                Clock.schedule_once(self.reset_button_text, 3)

        except Exception as e:
            logger.error(f"Error requesting ticket: {str(e)}")
            self.ticket_button.text = "Network Error"
            Clock.schedule_once(self.reset_button_text, 3)

    def reset_button_text(self, dt):
        """Reset the button text after displaying feedback"""
        self.ticket_button.text = "Request New Ticket"

    def update_current_number(self, dt):
        """Update the currently called number display"""
        try:
            response = requests.get(f"{self.api_url}/currently_called")

            if response.status_code == 200:
                data = response.json()
                current = data.get("currently_called", "---")

                # Update the display
                self.current_number.text = str(current)
            else:
                logger.error(f"Failed to get current number: {response.status_code}")

        except Exception as e:
            logger.error(f"Error updating current number: {str(e)}")


class TicketingApp(App):
    def build(self):
        # Enable fullscreen mode
        Window.fullscreen = 'auto'
        return TicketingSystem()


if __name__ == '__main__':
    TicketingApp().run()