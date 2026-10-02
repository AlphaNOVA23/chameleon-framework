import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import config_store

def send_threat_email_alert(session_id: str, classification: str, src_ip: str, command: str = "", user_id: str = "default_user"):
    """
    Sends an email alert to the configured SOC alert email address when
    a Tier 2 AI Agent or Tier 3 Human attacker is trapped.
    """
    settings = config_store.load_settings(user_id)
    recipient_email = settings.get("alert_email", "").strip()
    
    if not recipient_email:
        print(f"[Email Alert] No alert email address configured. Skipping alert for session {session_id}.")
        return False

    import os
    smtp_host = settings.get("smtp_host") or os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(settings.get("smtp_port") or os.environ.get("SMTP_PORT", 587))
    smtp_user = settings.get("smtp_user") or os.environ.get("SMTP_USER", "")
    smtp_pass = settings.get("smtp_password") or os.environ.get("SMTP_PASSWORD", "")

    subject = f"🚨 CHAMELEON ALERT: {classification} Threat Detected from {src_ip}"
    
    body = f"""
========================================================================
CHAMELEON ENTERPRISE DECEPTION — AUTOMATED THREAT ALERT
========================================================================

Alert Level     : HIGH / SEVERE
Threat Category : {classification}
Attacker IP     : {src_ip}
Session ID      : {session_id}
Latest Command  : {command or 'Session Initiated'}

SYSTEM ACTION DEPLOYED:
- Dynamic Biometric Profiling active.
- Generative Honeytoken Deception active.

Log into your Chameleon SOC Radar Dashboard to view full live forensics:
https://leon-1234d.web.app

========================================================================
    """

    print(f"[Email Alert] Dispatching security alert to {recipient_email} for IP {src_ip}...")

    # If SMTP credentials are provided, send live email; otherwise log alert payload
    if smtp_user and smtp_pass:
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(smtp_host, smtp_port, timeout=5)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            server.quit()
            print(f"[Email Alert] Successfully sent email to {recipient_email}")
            return True
        except Exception as e:
            print(f"[Email Alert] Failed to send email via SMTP: {e}")
            return False
    else:
        print(f"[Email Alert Simulated] Alert payload generated for {recipient_email}:\n{subject}")
        return True
