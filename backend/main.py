import os
import smtplib
import ssl
from email.message import EmailMessage
from dotenv import load_dotenv
from pathlib import Path

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.middleware.cors import CORSMiddleware

# Load environment variables explicitly from backend/.env
load_dotenv(dotenv_path=Path(__file__).with_name('.env'))

SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
MAIL_FROM = os.getenv("MAIL_FROM")
MAIL_TO = os.getenv("MAIL_TO")
USE_TLS = os.getenv("USE_TLS", "true").lower() == "true"

# Safe startup log (no secrets)
print(f"[CONFIG] MAIL_FROM={MAIL_FROM}, MAIL_TO={MAIL_TO}, SMTP_USER_SET={bool(SMTP_USERNAME)}, TLS={USE_TLS}")


def _validate_payload(data: dict) -> tuple[bool, str | None]:
    required = ["name", "email", "subject", "message"]
    for k in required:
        if not isinstance(data.get(k), str) or not data.get(k).strip():
            return False, f"Missing or empty field: {k}"
    # simple bounds
    if len(data["name"]) > 100:
        return False, "name too long"
    if len(data["subject"]) > 150:
        return False, "subject too long"
    if len(data["message"]) > 4000:
        return False, "message too long"
    # naive email check
    if "@" not in data["email"] or "." not in data["email"]:
        return False, "invalid email"
    return True, None


async def health(request: Request):
    return JSONResponse({"status": "ok"})


def send_mail_via_smtp(subject: str, body: str, reply_to: str | None = None):
    missing = [k for k, v in {
        "SMTP_USERNAME": SMTP_USERNAME,
        "SMTP_PASSWORD": SMTP_PASSWORD,
        "MAIL_FROM": MAIL_FROM,
        "MAIL_TO": MAIL_TO,
    }.items() if not v]
    if missing:
        raise RuntimeError(f"Email config missing: {', '.join(missing)}")

    msg = EmailMessage()
    msg["From"] = MAIL_FROM
    msg["To"] = MAIL_TO
    msg["Subject"] = subject
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(body)

    print(f"[SMTP] Connecting to {SMTP_SERVER}:{SMTP_PORT} (TLS={USE_TLS}) to send to {MAIL_TO}")
    if USE_TLS:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            server.set_debuglevel(0)
            server.ehlo()
            print("[SMTP] Starting TLS...")
            server.starttls(context=context)
            server.ehlo()
            print(f"[SMTP] Logging in as {SMTP_USERNAME}...")
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            print("[SMTP] Logged in. Sending message...")
            server.send_message(msg)
            print("[SMTP] Message sent successfully.")
    else:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            server.set_debuglevel(0)
            print(f"[SMTP] Logging in as {SMTP_USERNAME} (SSL)...")
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            print("[SMTP] Logged in. Sending message...")
            server.send_message(msg)
            print("[SMTP] Message sent successfully.")


async def contact(request: Request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"detail": "Invalid JSON"}, status_code=400)

    # Honeypot spam check
    if isinstance(data.get("honeypot"), str) and data.get("honeypot").strip():
        return JSONResponse({"ok": True})

    ok, err = _validate_payload(data)
    if not ok:
        return JSONResponse({"detail": err}, status_code=400)

    subject = f"Portfolio Contact: {data['subject']}"
    body = (
        "New contact message from your portfolio website\n\n"
        f"Name: {data['name']}\n"
        f"Email: {data['email']}\n"
        f"Subject: {data['subject']}\n\n"
        f"Message:\n{data['message']}\n"
    )

    try:
        send_mail_via_smtp(subject, body, reply_to=data.get("email"))
        return JSONResponse({"ok": True})
    except Exception as e:
        return JSONResponse({"detail": f"Failed to send email: {e}"}, status_code=500)


routes = [
    Route("/health", health),
    Route("/contact", contact, methods=["POST"]),
]

app = Starlette(routes=routes)

# CORS (open in dev; tighten for prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Run: uvicorn main:app --reload --port 8000
