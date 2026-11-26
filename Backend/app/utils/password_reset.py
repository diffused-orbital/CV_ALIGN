import hashlib
import logging
import smtplib
import ssl
import time
from email.message import EmailMessage
from urllib.parse import quote

from fastapi import HTTPException
from sqlalchemy import delete
from sqlalchemy.dialects.sqlite import insert

from app import config
from app.models.password_reset import AuthRateLimit, PasswordReset
from app.database import SessionLocal

logger = logging.getLogger(__name__)


def token_hash(value):
    return hashlib.sha256(value.encode()).hexdigest()


def check_rate_limit(db, key, limit):
    """Persist the limit so workers and restarts share the same counters."""
    window = int(time.time()) // 3600
    key = token_hash(key)
    statement = insert(AuthRateLimit).values(key=key, window=window, count=1)
    statement = statement.on_conflict_do_update(
        index_elements=[AuthRateLimit.key],
        set_={"window": window, "count": AuthRateLimit.count + 1},
        where=AuthRateLimit.window == window,
    )
    # Expired counters are removed inside the same SQLite write transaction.
    db.execute(delete(AuthRateLimit).where(AuthRateLimit.window < window))
    db.execute(statement)
    count = db.get(AuthRateLimit, key).count
    db.commit()
    if count > limit:
        raise HTTPException(429, "Too many requests. Please try again later.", headers={"Retry-After": "3600"})


def send_reset_email(email, token, token_digest):
    message = EmailMessage()
    message["Subject"] = "Reset your CV_ALIGN password"
    message["From"] = config.SMTP_FROM
    message["To"] = email
    url = f"{config.FRONTEND_URL}/forgot-password#token={quote(token)}"
    message.set_content(f"Open this link to reset your password within 15 minutes.\n\n{url}\n\nIf you did not request this, you can ignore this email.")
    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=15) as smtp:
            if config.SMTP_STARTTLS:
                smtp.starttls(context=ssl.create_default_context())
            if config.SMTP_USERNAME:
                smtp.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            smtp.send_message(message)
    except Exception:
        # A failed delivery must not leave a usable reset token behind.
        with SessionLocal() as db:
            db.execute(delete(PasswordReset).where(PasswordReset.token_hash == token_digest))
            db.commit()
        logger.error("Password-reset email delivery failed. Check the SMTP configuration.")
