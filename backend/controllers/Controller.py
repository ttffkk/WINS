# /wins/backend/app.py (Entry point)
"""Main application entry point for the ticketing system."""
import uvicorn
from fastapi import FastAPI
from backend.controllers.api_controller import router as api_router
from backend.controllers.web_controller import router as web_router
from backend.services.ticket_service import init_db

app = FastAPI(title="Ticketing System")

# Include routers
app.include_router(api_router, prefix="/api")
app.include_router(web_router)

if __name__ == "__main__":
    # Initialize database on startup
    init_db()
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)

# /wins/backend/controllers/api_controller.py (API endpoints)
"""Controller for API endpoints handling ticket operations."""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from backend.services.ticket_service import (
    create_ticket,
    call_next_ticket,
    get_currently_called,
    get_ticket_history,
    reset_queue,
    get_queue_status
)

router = APIRouter(tags=["api"])


@router.post("/new_ticket")
async def create_new_ticket() -> Dict[str, Any]:
    """Create a new ticket and return its details."""
    result = create_ticket()
    if not result:
        raise HTTPException(status_code=500, detail="Ticket creation failed.")
    return result


@router.get("/queue_status")
async def get_status() -> Dict[str, int]:
    """Get the current queue status."""
    return get_queue_status()


@router.post("/call_next")
async def call_next() -> Dict[str, Any]:
    """Call the next ticket in the queue."""
    result = call_next_ticket()
    if not result:
        raise HTTPException(status_code=404, detail="No ticket to call.")
    return result


@router.get("/currently_called")
async def currently_called() -> Dict[str, Any]:
    """Get the most recently called ticket."""
    return get_currently_called()


@router.get("/ticket_history")
async def ticket_history(limit: int = 10) -> List[Dict[str, Any]]:
    """Get history of called tickets with timestamps."""
    return get_ticket_history(limit)


@router.post("/reset_queue")
async def reset() -> Dict[str, bool]:
    """Reset the queue by marking all tickets as attended."""
    success = reset_queue()
    if not success:
        raise HTTPException(status_code=500, detail="Failed to reset queue.")
    return {"success": success}


# /wins/backend/controllers/web_controller.py (Web UI endpoints)
"""Controller for web interface endpoints."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from backend.services.ticket_service import (
    get_queue_status,
    get_currently_called,
    get_ticket_history
)

# Set up paths for templates
BACKEND_DIR = Path(__file__).parent.parent
templates = Jinja2Templates(directory=str(BACKEND_DIR / "templates"))

router = APIRouter(tags=["web"])


@router.get("/", response_class=HTMLResponse)
async def staff_dashboard(request: Request):
    """Render the staff dashboard."""
    queue_status = get_queue_status()
    current = get_currently_called()
    history = get_ticket_history(5)  # Show last 5 called tickets

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "queue_status": queue_status,
            "current": current,
            "history": history
        }
    )


# /wins/backend/services/ticket_service.py (renamed from Services.py)
"""Service for ticket management and database operations."""
from datetime import datetime
from typing import Dict, Any, Optional, List
import duckdb
from pathlib import Path

# Use a dedicated DB directory
DB_DIR = Path(__file__).parent.parent / "db"
DB_DIR.mkdir(exist_ok=True)  # Ensure directory exists
DUCKDB_DATABASE = str(DB_DIR / "tickets.duckdb")


def init_db():
    """Initialize the database with the tickets table."""
    conn = duckdb.connect(DUCKDB_DATABASE)
    try:
        # Create tickets table
        conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_personid START 1;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER,
                ticket_number INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                attended BOOLEAN DEFAULT FALSE,
                PRIMARY KEY (id)
            );
        """)
        conn.commit()
        print("Database initialized successfully.")
    except Exception as e:
        try:
            conn.rollback()
        except:
            pass  # Ignore if no transaction is active
        print(f"[ERROR] init_db: {e}")
    finally:
        conn.close()


# [Rest of your service functions remain the same]

# /wins/backend/models/ticket.py (New file for data models)
"""Data models for the ticketing system."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class Ticket(BaseModel):
    """Model representing a ticket."""
    id: Optional[int] = None
    ticket_number: int
    timestamp: datetime
    attended: bool = False


class TicketResponse(BaseModel):
    """Response model for ticket operations."""
    ticket_number: int
    timestamp: str
    attended: bool = False


class QueueStatus(BaseModel):
    """Model representing the queue status."""
    waiting_tickets: int
    total_issued: int
    highest_ticket: int


class CalledTicket(BaseModel):
    """Model representing a called ticket."""
    called_ticket: int
    called_time: str
    wait_time_seconds: float


# /wins/backend/config/settings.py (New file for configuration)
"""Configuration settings for the ticketing system."""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings."""
    # Basic app settings
    APP_NAME: str = "Ticketing System"
    DEBUG_MODE: bool = True

    # Database settings
    DB_NAME: str = "tickets.duckdb"
    DB_DIR: Path = Path(__file__).parent.parent / "db"

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Kivy app settings
    KIVY_AUTO_START: bool = True

    class Config:
        env_file = ".env"


settings = Settings()

# /wins/kivy_app/main.py (renamed from kivy_app.py)
"""Main entry point for the Kivy application."""
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
import requests
import json

SERVER_URL = "http://localhost:8000/api"


class TicketingApp(App):
    """Main application class for the ticketing kiosk."""

    def build(self):
        """Build the UI layout."""
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Title
        layout.add_widget(Label(
            text='Ticketing Kiosk',
            font_size=24,
            size_hint=(1, 0.2)
        ))

        # Current ticket display
        self.current_ticket_label = Label(
            text='Currently Called: None',
            font_size=36,
            size_hint=(1, 0.4)
        )
        layout.add_widget(self.current_ticket_label)

        # New ticket button
        new_ticket_button = Button(
            text='Get New Ticket',
            font_size=24,
            size_hint=(1, 0.3),
            background_color=(0.2, 0.6, 1, 1)
        )
        new_ticket_button.bind(on_press=self.request_new_ticket)
        layout.add_widget(new_ticket_button)

        # Start polling for updates
        self.update_current_ticket()

        return layout

    def request_new_ticket(self, instance):
        """Request a new ticket from the server."""
        try:
            response = requests.post(f"{SERVER_URL}/new_ticket")
            if response.status_code == 200:
                ticket_data = response.json()
                ticket_number = ticket_data['ticket_number']
                self.print_ticket(ticket_number, ticket_data['timestamp'])
            else:
                print(f"Error: {response.status_code}")
        except Exception as e:
            print(f"Error requesting ticket: {e}")

    def update_current_ticket(self):
        """Update the currently called ticket display."""
        try:
            response = requests.get(f"{SERVER_URL}/currently_called")
            if response.status_code == 200:
                data = response.json()
                if data.get('currently_called'):
                    self.current_ticket_label.text = f"Currently Called: {data['currently_called']}"
                else:
                    self.current_ticket_label.text = "Currently Called: None"
        except Exception as e:
            print(f"Error updating current ticket: {e}")

        # Schedule next update
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self.update_current_ticket(), 5)

    def print_ticket(self, ticket_number, timestamp):
        """Print a ticket with the given number and timestamp."""
        # This would interface with a physical printer
        # For now, just print to console
        print(f"Printing ticket: {ticket_number} - {timestamp}")


if __name__ == '__main__':
    TicketingApp().run()