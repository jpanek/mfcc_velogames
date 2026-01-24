# utils/email_functions.py

import os
import sys
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from config import Config
except ImportError:
    # Fallback for specific execution environments
    sys.path.append(os.getcwd())
    from config import Config

def send_email(recipient, subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = formataddr(("MFCC Velogames", Config.MAIL_USERNAME))
    msg['To'] = recipient

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            smtp.send_message(msg)
            print(f"Email sent successfully to {recipient}!")
    except smtplib.SMTPAuthenticationError:
        print("Authentication Error: Check your Gmail App Password in config.py.")
    except Exception as e:
        print(f"Failed to send email: {e}")


#print(Config.MAIL_USERNAME)
#print(Config.MAIL_PASSWORD)

now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

#recipients = ['juraj.panek@gmail.com', 'janieh87@gmail.com']
recipients = ['juraj.panek@gmail.com']
recipients_string = ", ".join(recipients)

print(recipients_string)

send_email(
    recipient=recipients_string, 
    subject='[TEST] MFCC Velogames results', 
    body=f"Results were updated as of {now}"
)
