from flask import g
from utils.db_functions import get_data_from_db
from utils.queries import sql_navbar
from datetime import datetime

def before_request():
    _, races = get_data_from_db(sql_navbar)
    g.races = races
