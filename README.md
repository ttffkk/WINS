
# WINS Ticketing System

**WINS** (**W**aiting **I**ssue **N**umber **S**ystem) is an all-in-one ticketing system designed to streamline queue management. This system provides a seamless experience for both customers and staff with real-time updates, intuitive interfaces, and efficient ticket handling.

## Features

- **Real-Time Ticket Updates**: Live updates for the currently called ticket number.
- **Kiosk-Based Ticketing**: A user-friendly touch-based kiosk for customers to request tickets.
- **Web-Based Staff Dashboard**: Manage queues efficiently with a responsive web interface.
- **ESC/POS Printer Integration**: Prints tickets via ESC/POS-compatible thermal printers.
- **Customizable Settings**: Flexible backend options for deployment and configuration.

## Technologies Used

### Core Programming Language
- **Python**: Used for backend development and the kiosk application.

### Backend Technologies
- **FastAPI**: High-performance framework for building APIs with Python.
- **WebSockets**: Enables real-time communication between the backend and kiosk application.
- **Gunicorn & uWSGI**: Production-ready HTTP servers for backend deployment.
- **Supervisor & systemd**: Tools for managing backend services.

### Customer Interface (Kiosk Application)
- **Kivy**: Multi-touch framework for creating the touch-based kiosk application.

### Staff Dashboard
- **HTML, CSS, JavaScript**: For a responsive and user-friendly dashboard.
- **Dashboard Functionality**:
  - Call the next ticket.
  - Reset the queue.
  - View ticket history.

### Printer Integration
- **python-escpos**: Library for thermal printer communication.

### Development Tools
- **Git**: For version control.
- **venv**: Virtual environment for dependency management.
- **Postman & curl**: API testing tools.

## Setup Guide

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/ttffkk/WINS.git
   cd WINS
   ```

2. **Backend Setup**:
   - Install dependencies:
     ```bash
     python -m venv venv
     source venv/bin/activate
     pip install -r requirements.txt
     ```
   - Run the FastAPI server:
     ```bash
     uvicorn app.main:app --reload
     ```

3. **Kiosk Application**:
   - Navigate to the `kivy_app/` directory.
   - Run the Kivy application:
     ```bash
     python kivy_app.py
     ```

4. **Access the Dashboard**:
   - Open your browser and navigate to `http://localhost:8000`.

## Usage Instructions

- **For Customers**:
  - Use the kiosk interface to request a ticket.
  - A ticket number will be printed using the thermal printer.

- **For Staff**:
  - Use the dashboard to manage the queue.
  - Call the next ticket or reset the queue as needed.

## API Documentation

The backend provides the following key endpoints:
- **`/queue_status`**: Get the current queue status.
- **`/currently_called`**: Retrieve the currently called ticket number.
- **`/call_next`**: Call the next ticket (POST request).
- **`/reset_queue`**: Reset the queue (POST request).

For detailed API documentation, visit the auto-generated FastAPI docs at `/docs`.

## Screenshots

_Add screenshots or GIFs here showcasing the kiosk interface and the web dashboard._

## Contributing

We welcome contributions! Please follow these steps:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature-name`).
3. Commit your changes (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature/your-feature-name`).
5. Open a pull request.

## License

This project is licensed under the [MIT License](LICENSE).
```

Let me know if you'd like any further adjustments or additional sections!
