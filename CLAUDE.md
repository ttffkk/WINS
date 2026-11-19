# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Process

This repo follows the shared process in `ttffkk/knowledge`. In this repo you are the **developer** role. Sprints are the scrum master's job, so they are not imported here.

@../knowledge/process/roles.md
@../knowledge/process/ticket-workflow.md
@../knowledge/process/ticket-guidelines.md
@../knowledge/process/definition-of-done.md
@../knowledge/clickup/tooling.md

If the imports fail, run `git -C ../knowledge pull`, or clone `ttffkk/knowledge` next to this repo.

What differs for WINS:

- **Branching:** the only branch today is `main`. There is no `develop` yet. Until Tim creates it, ask him (assigned comment on the ticket) before you open the first PR; don't create `develop` yourself.
- **Deploy:** none. There is no CI (`.github/` doesn't exist) and no automated rollout. Tim installs on the Debian kiosk box by hand. The `Closed` deploy criterion means Tim confirms it runs there.
- **Monitoring:** none. The only signals are the backend's console output and `kivy_app.log` on the kiosk. The 24 h no-errors check is Tim reading those.
- **Testing on the dev box:** no tests or linter. Use `python -m py_compile <file>` and, where pycups is installed, an import of `backend.controllers.Controller`. The printer can't be tested on Windows; say so in the handoff.

## Project

WINS (Waiting Issue Number System) is a queue-ticketing system with three parts: a FastAPI backend with a server-rendered staff dashboard, a Kivy touch kiosk for customers, and a thermal-printer module that prints each new ticket. The target deployment is Linux/Debian (the printer code relies on CUPS and `/dev/*` device paths).

## Commands

Install dependencies:
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Run the backend **from the repo root**. `Controller.py` uses a relative import (`from ..services.Services import ...`) and `Services.py` uses an absolute one (`from backend.print.thermal_printer import ...`), so it only works when the repo root is on the path:
```bash
python -m backend.controllers.Controller            # runs init_db() and then serves on 0.0.0.0:8000
uvicorn backend.controllers.Controller:app --reload # dev reload; does NOT call init_db()
```
The README's `uvicorn app.main:app` is out of date: there is no `app/` package.

Run the kiosk (it expects the backend at `http://localhost:8000`):
```bash
python kivy_app/kivy_app.py
```

Test the printer on its own: `python -m backend.print.thermal_printer`.

The repo has no tests, linter or build config. The dashboard is at `/` and the FastAPI docs are at `/docs`.

## Architecture

- **`backend/controllers/Controller.py`** creates the FastAPI `app`. It mounts `backend/static` and `backend/templates` (Jinja2) using paths computed from `__file__`. JSON endpoints live on an `APIRouter`: `POST /new_ticket`, `GET /queue_status`, `POST /call_next`, `GET /currently_called`, `GET /ticket_history?limit=`, `POST /reset_queue`. `GET /` renders `dashboard.html` with the initial state.
- **`backend/services/Services.py`** holds all business logic and persistence as module-level functions over **DuckDB**. Every function opens and closes its own connection. When something fails, these functions return `None`, empty or zeroed values, or `False` instead of raising, and the controller turns those into HTTP errors.
  - The DB file is `tickets.duckdb`, a path relative to the **current working directory** (it is gitignored).
  - There is a single `tickets` table (`id`, `ticket_number`, `timestamp`, `attended`). `id` comes from the sequence `seq_personid`. A ticket is "waiting" when `attended = FALSE`. Calling the next ticket sets the oldest waiting ticket to `attended = TRUE`. The "currently called" ticket is the attended ticket with the highest `id`. Resetting the queue marks every ticket attended. Ticket numbers keep increasing and never restart.
  - `create_ticket()` builds a `ThermalPrinter()` and prints synchronously on every request, so the printer module is imported and run on the request path.
- **`backend/print/thermal_printer.py`** (`ThermalPrinter`) draws the ticket with Pillow: the SVG logo (`Mediamodifier-Design.svg`, converted with CairoSVG), then the number, then a timestamp. It then tries several print paths in order: a CUPS printer (it prefers names containing "CAPD"/"245"), then raw `/dev/usb/lp*` / `/dev/lp*` / `/dev/ttyS*` / `/dev/ttyUSB*` devices through python-escpos or raw ESC/POS bytes, then `lp`/`lpr`. It imports `cups` at the top of the module, so the backend will fail to import if pycups/libcups is missing (for example on a plain Windows install).
- **`kivy_app/kivy_app.py`** is a fullscreen kiosk. It polls `GET /currently_called` every second and posts to `/new_ticket` when the button is pressed. It logs to `kivy_app.log` in the working directory.
- **Dashboard** (`backend/templates/dashboard.html` extends `base.html`; `backend/static/js/dashboard.js`): the first render happens on the server. After that, the JS polls `/queue_status`, `/currently_called` and `/ticket_history?limit=5` every 5 seconds and wires up the Call Next and Reset buttons. Nothing uses WebSockets yet, although the README mentions them. All real-time updates come from polling.
