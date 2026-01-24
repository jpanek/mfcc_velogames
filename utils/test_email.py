#print(Config.MAIL_USERNAME)
#print(Config.MAIL_PASSWORD)

from email_functions import send_email, email_stage_body
from db_functions import get_data_from_db
from queries import sql_stage_results, sql_gc_results

#recipients = ['juraj.panek@gmail.com', 'janieh87@gmail.com']
recipients = ['juraj.panek@gmail.com']
recipients_string = ", ".join(recipients)

stage_id = 698
params = (stage_id,)


race_name = "Tour Down Under"
stage_name = "Stage 4"
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

email_subject = f"{race_name} - {stage_name} - results"

send_email(recipient=recipients_string, subject=email_subject, body=email_body)
