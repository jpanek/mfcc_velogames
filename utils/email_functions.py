# utils/email_functions.py

import os
import sys
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from datetime import datetime
from db_functions import get_data_from_db
from queries import sql_stage_results, sql_gc_results


# ---------------------------- MOVE TO CONFIG ----------------------------
#recipients = ['juraj.panek@gmail.com', 'janieh87@gmail.com']
recipients = ['juraj.panek@gmail.com']
recipients_string = ", ".join(recipients)
# ---------------------------- MOVE TO CONFIG ----------------------------

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from config import Config
except ImportError:
    # Fallback for specific execution environments
    sys.path.append(os.getcwd())
    from config import Config

def send_email(recipient, subject, body):
    msg = EmailMessage()
    
    # 1. Set a plain-text fallback for preview snippets/basic clients
    msg.set_content("Please use an HTML-compatible email client to view these results.")
    
    # 2. Add the HTML version
    msg.add_alternative(body, subtype='html')

    msg['Subject'] = subject
    msg['From'] = formataddr(("MFCC Velogames", Config.MAIL_USERNAME))
    msg['To'] = recipient

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            smtp.send_message(msg)
            print(f"\t** [EMAIL] Email sent successfully to {recipient}")
    except smtplib.SMTPAuthenticationError:
        print("\t** [EMAIL] Authentication Error: Check your Gmail App Password in config.py.")
    except Exception as e:
        print(f"\t** [EMAIL] Failed to send email: {e}")

def email_stage_body(race_name, stage_name, columns, data, columns_gc, data_gc):
    def build_table(cols, rows):
        header = "".join([f"<th style='border: 1px solid #ddd; padding: 12px; text-align: left; background-color: #f8f9fa;'>{col}</th>" for col in cols[4:]])
        
        body_rows = ""
        for row in rows:
            body_rows += "<tr>"
            for item in row[4:]:
                # Check if item is a number (int or float)
                if isinstance(item, (int, float)):
                    formatted_item = f"{item:,}"
                else:
                    formatted_item = item
                    
                body_rows += f"<td style='border: 1px solid #ddd; padding: 8px;'>{formatted_item}</td>"
            body_rows += "</tr>"
        
        return f"<table style='width: 100%; border-collapse: collapse; margin-bottom: 30px;'><thead><tr>{header}</tr></thead><tbody>{body_rows}</tbody></table>"

    stage_table = build_table(columns, data)
    gc_table = build_table(columns_gc, data_gc)

    html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #ffffff; padding: 20px;">
            <div style="max-width: 700px; margin: auto; border: 1px solid #eee; padding: 25px; border-radius: 8px;">
            <h2 style="color: #2c3e50; border-bottom: 3px solid #e67e22; padding-bottom: 10px; margin-top: 0;">{race_name}</h2>
            
            <h3 style="color: #d35400;">Stage Results: {stage_name}</h3>
            {stage_table}
            
            <h3 style="color: #2980b9;">GC after {stage_name}</h3>
            {gc_table}
            
            <div style="margin-top: 20px; text-align: center;">
                <a href="https://cyclingdatahub.com" style="background-color: #2980b9; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">View Full Standings</a>
            </div>

            <p style="font-size: 0.85em; color: #7f8c8d; border-top: 1px solid #eee; margin-top: 25px; padding-top: 15px;">
                Sent by MFer | <a href="https://cyclingdatahub.com" style="color: #7f8c8d;">cyclingdatahub.com</a><br>
                Updated at: {datetime.now().strftime("%H:%M:%S on %d-%m-%Y")}
            </p>
            </div>
        </body>
        </html>
        """
    return html

def send_email_stage_results(race, stage):
    race_name = race['name']
    stage_name = stage['stage_name']
    stage_id = stage['stage_id']

    params = (stage_id,)

    columns, data = get_data_from_db(sql_stage_results, params)
    columns_gc, data_gc = get_data_from_db(sql_gc_results, params)

    email_body = email_stage_body(
        race_name=race_name,
        stage_name=stage_name,
        columns=columns,
        data = data,
        columns_gc=columns_gc,
        data_gc=data_gc
    )

    email_subject = f"[MFCC] {race_name} - {stage_name} - results"

    recipients_string = ", ".join(Config.RECIPIENTS)

    send_email(recipient=recipients_string, subject=email_subject, body=email_body)