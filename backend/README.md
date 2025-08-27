# Portfolio Contact Backend (FastAPI)

A minimal FastAPI backend to send contact emails from your portfolio site using SMTP via `fastapi-mail`.

## Requirements
- Python 3.10+
- SMTP account (e.g., Gmail with App Password, Outlook, AWS SES SMTP, etc.)

## Setup
1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in values:
   ```ini
   SMTP_USERNAME=your_smtp_username
   SMTP_PASSWORD=your_smtp_password
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   USE_TLS=true
   MAIL_FROM=your_sender_email@example.com
   MAIL_TO=your_destination_inbox@example.com
   ```
   Notes:
   - Gmail: create an App Password and use it for `SMTP_PASSWORD` (Account → Security → App Passwords).
   - AWS SES: use your SES SMTP credentials and server (e.g., `email-smtp.us-east-1.amazonaws.com`). Ensure `MAIL_FROM` is a verified sender/domain.

## Run the server
```bash
uvicorn main:app --reload --port 8000
```

- Health check: `GET http://127.0.0.1:8000/health`
- Contact endpoint: `POST http://127.0.0.1:8000/contact`

## Frontend wiring
The site posts to `http://127.0.0.1:8000/contact` by default. To override in production, set a global in your HTML before loading `script.js`:
```html
<script>window.PORTFOLIO_API_BASE = 'https://api.yourdomain.com';</script>
```

The contact form in `index.html` includes a hidden honeypot input named `honeypot` for basic spam protection.

## Security recommendations
- Restrict CORS origins in `main.py` for production.
- Rate limit or add CAPTCHA if you see abuse.
- Avoid logging message bodies to stdout.
- Use a dedicated SMTP user with least privileges.
