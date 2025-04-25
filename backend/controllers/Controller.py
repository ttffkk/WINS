from pathlib import Path
from typing import Dict, Any, List

from fastapi import FastAPI, APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Import services directly from the Services module
# Replace the import line with:
from ..services.Services import (
    create_ticket,
    call_next_ticket,
    get_currently_called,
    get_ticket_history,
    reset_queue,
    init_db,
    get_queue_status
)

app = FastAPI()
router = APIRouter()

# Set up paths for templates and static files
# Use Path for better cross-platform path handling
ROOT_DIR = Path(__file__).parent.parent.parent  # WINS directory
BACKEND_DIR = ROOT_DIR / "backend"

# Set up templates
templates = Jinja2Templates(directory=str(BACKEND_DIR / "templates"))

# Mount static files
app.mount("/static", StaticFiles(directory=str(BACKEND_DIR / "static")), name="static")


# Keep your existing API endpoints
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


# Add new web interface route
@app.get("/", response_class=HTMLResponse)
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


app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    # Initialize database on startup
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)