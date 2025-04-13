# WINS Ticketing System

**WINS** (**W**aiting **I**ssue **N**umber **S**ystem) is an all-in-one ticketing system built using a variety of modern technologies to provide a seamless experience for both customers and staff.

## Technologies Used

This project leverages the following key technologies:

**Core Programming Language:**

* **Python:** The primary programming language used for both the backend and the Kivy application.

**Backend Technologies:**

* **Backend Framework (Choice):**
    * **FastAPI:** A modern, high-performance web framework for building APIs with Python 3.7+ based on standard Python type hints.
* **WebSockets (Optional):** For real-time communication between the backend and the Kivy application, potentially used for instant updates on the called ticket number.
* **HTML:** Used for creating the structure of the staff web interface.
* **CSS:** Used for styling the staff web interface to provide a user-friendly experience.
* **Backend Deployment:**
    * **Gunicorn:** A Python WSGI HTTP server for serving Flask or FastAPI applications.
    * **uWSGI:** A fast and production-ready server for web applications.
    * **Supervisor:** A process control system that allows for monitoring and controlling processes.
    * **systemd:** A system and service manager for Linux operating systems, used for managing backend services.
* **Backend Testing:**
    * **curl:** A command-line tool for making HTTP requests to test API endpoints.
    * **Postman:** A popular API client for testing and exploring APIs.
* **Logging:** Python's built-in `logging` module for recording events and debugging.

**Customer Interface (Kiosk Application):**

* **Kivy:** An open-source Python framework for developing multi-touch applications with a natural user interface. Used to create the touch-based kiosk application for customers to request tickets.

**Printer Integration:**

* **`python-escpos`:** A Python library for communicating with ESC/POS compatible thermal printers, used for printing the ticket slips.

**System and Development Environment:**

* **Debian:** The chosen Linux operating system for the target hardware.
* **`venv`:** Python's built-in module for creating isolated virtual environments to manage project dependencies.
* **Git:** A distributed version control system for tracking changes in the codebase.
* **Project Repository (Optional but Recommended):** Platforms like GitHub, GitLab, or Bitbucket for hosting the Git repository and facilitating collaboration.
* **SSH:** Secure Shell protocol for secure remote access to the Debian machine.
* **Code Editor/IDE:** A development environment chosen by the developers for writing and managing the code.

**System Management:**

* **systemd:** Used for managing the Kivy application as a service, ensuring it runs on boot and can automatically restart on failure.

This combination of technologies allows for a robust, user-friendly, and efficient ticketing system. The choice between Flask and FastAPI for the backend provides flexibility based on project requirements and developer preference. The use of Kivy enables the creation of an intuitive touch-based interface for customers, while the staff web interface offers a convenient way for staff to manage the queue.
