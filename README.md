# NAYA Bubble Laundry Management System

A web-based system that lets a laundry shop owner manage customers.
Built with Flask, MySQL, Bootstrap and JavaScript.

## Features
- Owner registration with email OTP verification
- Secure login, logout and session timeout
- Dashboard with customer statistics
- Profile management and password change
- Customer management (add, view, search, edit, delete)
- Server-side and client-side validation
- Responsive design

## Security
- Passwords hashed with Werkzeug
- CSRF protection on every form
- Parameterized SQL queries (SQL injection protection)
- Jinja2 auto-escaping (XSS protection)
- Login lockout after 5 failed attempts
- 30-minute session timeout and security headers

## Requirements
- Python 3.10 or newer
- MySQL (XAMPP works)
- A Gmail account with an App Password (for OTP emails)

## Setup
1. Clone the repository and open the project folder.
2. Create and activate a virtual environment:

       python -m venv venv
       venv\Scripts\activate

3. Install dependencies:

       pip install -r requirements.txt

4. Start MySQL, open phpMyAdmin, and import `schema.sql`.
5. Copy `.env.example` to `.env` and fill in your values
   (Gmail address, App Password, a random SECRET_KEY, MySQL port).
6. Run the app:

       python app.py

7. Open http://127.0.0.1:5000

## Project structure
    app.py            application setup and error handlers
    config.py         settings loaded from .env
    database.py       MySQL connection helper
    extensions.py     shared CSRF and mail objects
    schema.sql        database tables
    models/           OOP classes (User, Customer, PendingRegistration)
    routes/           Flask blueprints (auth, dashboard, profile, customer)
    templates/        HTML pages
    static/           CSS, JavaScript, images

## Client interview
- Client: [ name and shop ]
- Date: [ date ]
- Needs they described: [ summary ]
- Client sign-off: [ confirmation that they reviewed and approved the system ]

## Author
[ your name, section, course ]