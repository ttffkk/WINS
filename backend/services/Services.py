from datetime import datetime
from typing import Dict, Any, Optional
from backend.print.thermal_printer import ThermalPrinter
import duckdb

DUCKDB_DATABASE = "tickets.duckdb"


def init_db():
    """Initialize the database with the tickets table."""
    conn = duckdb.connect(DUCKDB_DATABASE)
    try:
        # Create tickets table with the three attributes you specified
        # Using IDENTITY instead of AUTOINCREMENT which is DuckDB's syntax
        conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS seq_personid START 1;
               """)
        conn.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER ,
                    ticket_number INTEGER NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    attended BOOLEAN DEFAULT FALSE,
                    PRIMARY KEY (id)
                );
                """)
        conn.commit()
        print("Database initialized successfully.")
    except Exception as e:
        # Only try to rollback if we're in a transaction
        try:
            conn.rollback()
        except:
            pass  # Ignore if no transaction is active
        print(f"[ERROR] init_db: {e}")
    finally:
        conn.close()


def get_connection():
    """Get a database connection."""
    return duckdb.connect(database=DUCKDB_DATABASE, read_only=False)


def create_ticket() -> Optional[Dict[str, Any]]:
    """Create a new ticket and return its details."""
    conn = get_connection()
    try:
        printer= ThermalPrinter()
        # Get current highest ticket number directly from tickets table
        result = conn.execute("SELECT MAX(ticket_number) FROM tickets").fetchone()[0]
        last_ticket = result if result is not None else 0
        new_ticket_number = last_ticket + 1
        timestamp = datetime.now()

        # Insert new ticket (not attended by default)
        conn.execute(
            "INSERT INTO tickets (id,ticket_number, timestamp, attended) VALUES (nextval('seq_personid'),?, ?, FALSE)",
            (new_ticket_number, timestamp)
        )
        conn.commit()
        printer.print(new_ticket_number, timestamp)

        return {"ticket_number": new_ticket_number, "timestamp": timestamp.isoformat(), "attended": False}
    except Exception as e:
        try:
            print(f"[ERROR] create_ticket: {e}")
            conn.rollback()
        except:
            pass  # Ignore if no transaction is active
        print(f"[ERROR] create_ticket: {e}")
        return None
    finally:
        conn.close()


def get_queue_status() -> Dict[str, int]:
    """Get the current queue status."""
    conn = get_connection()
    try:
        # Count unattended tickets
        waiting_count = conn.execute("SELECT COUNT(*) FROM tickets WHERE attended = FALSE").fetchone()[0]
        # Get total tickets ever issued
        total_issued = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        # Get the highest ticket number
        result = conn.execute("SELECT MAX(ticket_number) FROM tickets").fetchone()[0]
        highest_number = result if result is not None else 0

        return {
            "waiting_tickets": waiting_count,
            "total_issued": total_issued,
            "highest_ticket": highest_number
        }
    except Exception as e:
        print(f"[ERROR] get_queue_status: {e}")
        return {"waiting_tickets": 0, "total_issued": 0, "highest_ticket": 0}
    finally:
        conn.close()


def call_next_ticket() -> Optional[Dict[str, Any]]:
    """Call the next ticket in the queue (oldest unattended ticket)."""
    conn = get_connection()
    try:
        # Get the oldest unattended ticket
        result = conn.execute(
            "SELECT id, ticket_number, timestamp FROM tickets WHERE attended = FALSE ORDER BY timestamp ASC LIMIT 1"
        ).fetchone()

        if not result:
            return None

        ticket_id, ticket_number, timestamp = result

        # Mark ticket as attended
        conn.execute("UPDATE tickets SET attended = TRUE WHERE id = ?", (ticket_id,))
        conn.commit()

        return {
            "called_ticket": ticket_number,
            "called_time": datetime.now().isoformat(),
            "wait_time_seconds": (datetime.now() - timestamp).total_seconds()
        }
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] call_next_ticket: {e}")
        return None
    finally:
        conn.close()


def get_currently_called() -> Dict[str, Any]:
    """Get the most recently called ticket."""
    conn = get_connection()
    try:
        # Get the most recently attended ticket
        result = conn.execute(
            "SELECT ticket_number, timestamp FROM tickets WHERE attended = TRUE ORDER BY id DESC LIMIT 1"
        ).fetchone()

        if not result:
            return {"currently_called": None}

        ticket_number, timestamp = result
        return {
            "currently_called": ticket_number,
            "called_at": timestamp.isoformat()
        }
    except Exception as e:
        print(f"[ERROR] get_currently_called: {e}")
        return {"currently_called": None}
    finally:
        conn.close()


def get_ticket_history(limit: int = 10) -> list:
    """Get history of called tickets with timestamps."""
    conn = get_connection()
    try:
        results = conn.execute(
            "SELECT ticket_number, timestamp FROM tickets WHERE attended = TRUE ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()

        history = [
            {"ticket_number": ticket_number, "called_at": timestamp.isoformat()}
            for ticket_number, timestamp in results
        ]

        return history
    except Exception as e:
        print(f"[ERROR] get_ticket_history: {e}")
        return []
    finally:
        conn.close()


def reset_queue() -> bool:
    """Reset the queue by marking all tickets as attended."""
    conn = get_connection()
    try:
        conn.execute("UPDATE tickets SET attended = TRUE")
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] reset_queue: {e}")
        return False
    finally:
        conn.close()
