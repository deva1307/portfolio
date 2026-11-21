import os
import re
import smtplib
import ssl
from email.message import EmailMessage

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import RequestEntityTooLarge


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
portfolio_origin = os.getenv("PORTFOLIO_ORIGIN", "https://deva1307.github.io").strip()
CORS(
    app,
    resources={r"/contact": {"origins": [portfolio_origin]}},
    methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


def _is_valid_email(value: str) -> bool:
    return bool(len(value) <= 254 and re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value))


def send_contact_email(name: str, email: str, subject: str, message: str) -> None:
    host = os.getenv("SMTP_HOST", "").strip()
    username = os.getenv("SMTP_USERNAME", "").strip()
    password = os.getenv("SMTP_PASSWORD", "")
    from_email = os.getenv("SMTP_FROM_EMAIL", "").strip()
    to_email = os.getenv("CONTACT_TO_EMAIL", "").strip()
    security = os.getenv("SMTP_SECURITY", "starttls").strip().lower()

    try:
        port = int(os.getenv("SMTP_PORT", "587"))
    except ValueError as exc:
        raise RuntimeError("SMTP_PORT must be a valid port number.") from exc

    required_settings = {
        "SMTP_HOST": host,
        "SMTP_USERNAME": username,
        "SMTP_PASSWORD": password,
        "SMTP_FROM_EMAIL": from_email,
        "CONTACT_TO_EMAIL": to_email,
    }
    missing_settings = [key for key, value in required_settings.items() if not value]
    if missing_settings:
        raise RuntimeError(
            "Email delivery is not configured. Missing settings: "
            + ", ".join(missing_settings)
            + "."
        )
    if not _is_valid_email(from_email) or not _is_valid_email(to_email):
        raise RuntimeError("SMTP_FROM_EMAIL and CONTACT_TO_EMAIL must be valid email addresses.")
    if not 1 <= port <= 65535:
        raise RuntimeError("SMTP_PORT must be between 1 and 65535.")
    if security not in {"ssl", "starttls"}:
        raise RuntimeError("SMTP_SECURITY must be either 'ssl' or 'starttls'.")

    email_message = EmailMessage()
    email_message["From"] = from_email
    email_message["To"] = to_email
    email_message["Reply-To"] = email
    email_message["Subject"] = f"Portfolio contact: {subject}"
    email_message.set_content(f"Name: {name}\nEmail: {email}\n\n{message}")

    context = ssl.create_default_context()
    if security == "ssl":
        smtp_connection = smtplib.SMTP_SSL(host, port, timeout=15, context=context)
    else:
        smtp_connection = smtplib.SMTP(host, port, timeout=15)

    with smtp_connection as server:
        if security == "starttls":
            server.starttls(context=context)
        server.login(username, password)
        server.send_message(email_message)


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.errorhandler(RequestEntityTooLarge)
def request_too_large(_error):
    return jsonify({"error": "The request is too large."}), 413


@app.post("/contact")
def contact():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "A JSON request body is required."}), 400

    if str(data.get("_honey") or "").strip():
        return jsonify({"error": "Invalid submission."}), 400

    name = str(data.get("name") or "").strip()
    email = str(data.get("email") or "").strip()
    subject = str(data.get("subject") or "").strip()
    message = str(data.get("message") or "").strip()
    if not all((name, email, subject, message)):
        return jsonify({"error": "Name, email, subject, and message are required."}), 400
    if any(
        len(value) > limit
        for value, limit in ((name, 100), (email, 254), (subject, 200), (message, 10000))
    ):
        return jsonify({"error": "One or more fields exceed the allowed length."}), 400
    if not _is_valid_email(email):
        return jsonify({"error": "Please provide a valid email address."}), 400
    if any(
        ord(char) < 32 or ord(char) == 127
        for value in (name, subject)
        for char in value
    ):
        return jsonify({"error": "Name and subject must not contain control characters."}), 400

    try:
        send_contact_email(name, email, subject, message)
    except RuntimeError as exc:
        app.logger.error("Contact email configuration error: %s", exc)
        return jsonify({"error": str(exc)}), 503
    except (smtplib.SMTPException, OSError):
        app.logger.exception("Contact email delivery failed")
        return jsonify({"error": "The message could not be sent. Please try again later."}), 502

    return jsonify({"message": "Your message was sent successfully."}), 200
