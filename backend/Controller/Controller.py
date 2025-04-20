from fastapi import FastAPI, APIRouter, HTTPException
from typing import Dict, Any, List
from backend.Services.Services import (
    create_ticket,
    call_next_ticket,
    get_currently_called,
    get_ticket_history,
    reset_queue,
    init_db, get_queue_status
)

app = FastAPI()
router = APIRouter()


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


app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    # Initialize database on startup
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)