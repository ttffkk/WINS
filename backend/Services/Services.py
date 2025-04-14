from datetime import datetime
import duckdb
from fastapi import Depends

DUCKDB_DATABASE = "tickets.duckdb"

def get_db():
    """Connects to the DuckDB database."""
    conn = duckdb.connect(database=DUCKDB_DATABASE, read_only=False)
    try:
        yield conn
    finally:
        conn.close()

def create_ticket(db_conn: duckdb.DuckDBPyConnection = Depends(get_db)):
    try:
        with db_conn.cursor() as cursor:
            cursor.execute("BEGIN TRANSACTION")

            cursor.execute("SELECT last_number FROM last_ticket")
            result = cursor.fetchone()
            last_ticket_number = result[0] if result else 0

            new_ticket_number = last_ticket_number + 1
            timestamp = datetime.now()

            cursor.execute("INSERT INTO ticket_queue (ticket_number, timestamp) VALUES (?, ?)",
                           (new_ticket_number, timestamp))
            cursor.execute("UPDATE last_ticket SET last_number = ?", (new_ticket_number,))

            db_conn.commit()
            return {"ticket_number": new_ticket_number, "timestamp": timestamp.isoformat()}
    except Exception as e:
        db_conn.rollback()
        return None  # Returning None to indicate an error

def get_queue_status(db_conn: duckdb.DuckDBPyConnection = Depends(get_db)):
    with db_conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM ticket_queue")
        count = cursor.fetchone()[0]
        return {"remaining_tickets": count}

def call_next_ticket(db_conn: duckdb.DuckDBPyConnection = Depends(get_db)):
    try:
        with db_conn.cursor() as cursor:
            cursor.execute("BEGIN TRANSACTION")
            cursor.execute("SELECT id, ticket_number, timestamp FROM ticket_queue ORDER BY id ASC LIMIT 1")
            next_ticket = cursor.fetchone()
            if next_ticket:
                ticket_id, ticket_number, timestamp = next_ticket
                cursor.execute("DELETE FROM ticket_queue WHERE id = ?", (ticket_id,))
                db_conn.commit()
                return {"called_ticket": ticket_number, "called_time": timestamp.isoformat()}
            else:
                return None
    except Exception as e:
        db_conn.rollback()
        return None

def get_currently_called(db_conn: duckdb.DuckDBPyConnection = Depends(get_db)):
    # We'll implement persistent storage for this later
    return {"currently_called": None}