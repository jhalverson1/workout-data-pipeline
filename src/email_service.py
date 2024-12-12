"""Email service for sending program output notifications."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

class EmailService:
    @staticmethod
    def send_email(program_output: str) -> None:
        """Sends email with program output."""
        msg = MIMEMultipart()
        msg["From"] = Config.GMAIL_ADDRESS
        msg["To"] = Config.GMAIL_RECIPIENT
        msg["Subject"] = "Workout Data Processing Completed"
        msg.attach(MIMEText(f"Processing output:\n\n{program_output}", "plain"))

        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(Config.GMAIL_ADDRESS, Config.GMAIL_PASSWORD)
                server.sendmail(Config.GMAIL_ADDRESS, Config.GMAIL_RECIPIENT, msg.as_string())
                print(f"Email sent to {Config.GMAIL_RECIPIENT}")
        except Exception as e:
            print(f"Failed to send email: {e}")
