from flask import g
from utils.db_functions import get_data_from_db
from datetime import datetime

def before_request():
    _, races = get_data_from_db("select name||'-'||substr(year,-2) as name, race_id from races where 0=0 order by end_date desc")
    g.races = races
