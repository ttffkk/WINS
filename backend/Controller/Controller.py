import duckdb
from fastapi import FastAPI, APIRouter, HTTPException, Depends

from backend.Services.Services import (
    create_ticket,
    get_queue_status,
    call_next_ticket,
    get_currently_called,
    get_db  # Import get_db here as well
)

app = FastAPI()
router = APIRouter()

@router.post("/new_ticket")
async def create_new_ticket_endpoint(db: duckdb.DuckDBPyConnection = Depends(get_db)):
    service_result = create_ticket(db)
    if service_result is None:
        raise HTTPException(status_code=500, detail="Failed to create new ticket")
    return service_result

@router.get("/queue_status")
async def get_queue_status_endpoint(db: duckdb.DuckDBPyConnection = Depends(get_db)):
    return get_queue_status(db)

@router.post("/call_next")
async def call_next_ticket_endpoint(db: duckdb.DuckDBPyConnection = Depends(get_db)):
    next_ticket = call_next_ticket(db)
    if next_ticket is None:
        raise HTTPException(status_code=404, detail="Queue is empty or an error occurred")
    return next_ticket

@router.get("/currently_called")
async def get_currently_called_endpoint(db: duckdb.DuckDBPyConnection = Depends(get_db)):
    return get_currently_called(db)

app.include_router(router)

# Example of how to run the FastAPI application (for local development)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)