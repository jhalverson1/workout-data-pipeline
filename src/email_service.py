import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

class EmailService:
    @staticmethod
    def send_email(program_output: str) -> None:
        """
        Sends an email containing the full output of the program.
        """
        sender_email = Config.GMAIL_ADDRESS
        receiver_email = Config.GMAIL_ADDRESS
        password = Config.GMAIL_PASSWORD

        subject = "Workout Data Processing Completed"
        body = f"The script has completed processing. Here is the output:\n\n{program_output}"

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, msg.as_string())
                print("Email sent successfully.")
        except Exception as e:
            print(f"Failed to send email: {e}")