from fastapi import FastAPI, APIRouter, HTTPException
from typing import List
from datetime import datetime

# Initialize FastAPI app and router
app = FastAPI()
router = APIRouter()

# In-memory ticket queue (replace with a more robust solution for production)
ticket_queue: List[int] = []
last_ticket_number: int = 0

# Endpoint to generate a new ticket
@router.post("/new_ticket")
async def create_new_ticket():
    """
    Receives a request for a new ticket, generates a unique ticket number,
    and adds it to the queue.
    """
    global last_ticket_number
    last_ticket_number += 1
    new_ticket_number = last_ticket_number
    ticket_queue.append(new_ticket_number)

    return {"ticket_number": new_ticket_number, "timestamp": datetime.now().isoformat()}

# Include the router in the main app
app.include_router(router)

# Example of how to run the FastAPI application (for local development)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)