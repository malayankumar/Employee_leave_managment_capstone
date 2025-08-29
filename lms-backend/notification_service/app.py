import os, smtplib
from email.mime.text import MIMEText
from flask import Flask, request, jsonify

app = Flask(__name__)

DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
SMTP_HOST = os.getenv("SMTP_HOST") or os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)
STARTTLS = os.getenv("SMTP_STARTTLS", "true").lower() == "true"

@app.post("/notify/email")
def notify_email():
    data = request.get_json(force=True) or {}
    to = data.get("to"); subject = data.get("subject"); body = data.get("body", "")
    if not (to and subject):
        return jsonify({"error": "to and subject required"}), 400

    if DRY_RUN:
        print(f"[DRY_RUN] would send to={to} subject={subject}")
        return jsonify({"status": "sent", "dry_run": True})

    try:
        msg = MIMEText(body or "", "plain", "utf-8")
        msg["From"] = FROM_EMAIL
        msg["To"] = to
        msg["Subject"] = subject

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
            s.ehlo()
            if STARTTLS:
                s.starttls()
                s.ehlo()
            if SMTP_USER and SMTP_PASS:
                s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(FROM_EMAIL, [to], msg.as_string())

        print(f"[MAIL] sent to={to} subject={subject}")
        return jsonify({"status": "sent"})
    except Exception as e:
        print(f"[MAIL][ERROR] {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
