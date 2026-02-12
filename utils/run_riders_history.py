# manual_inserts.py 

import sqlite3,os,sys
from datetime import datetime
import time as time_pkg
import random
import requests
import sys

#BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#sys.path.append(BASE_DIR)

#from config import db_path

from db_functions import get_db_path
from db_functions import get_races_db, get_teams_db, get_stages_db, get_roster_db, propagate_roster_db
from db_functions import insert_riders_db, insert_stages_db, insert_teams_db, insert_roster_db
from web_functions import get_riders, get_stages, get_teams, get_roster
from web_functions import get_riders_2


#races = get_races_db('Murcia')
races = get_races_db()


for race in races:
    time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Working on race: {race['name']} started at {time}")
    
    with requests.Session() as session:

        #load all riders
        if 1:
            riders_data = get_riders(race['url'], session=session)
            insert_riders_db(race, riders_data)
            print(f'\t\t Loaded {len(riders_data)} riders')
            
            wait = random.uniform(10, 30)
            print(f'\t\t Waiting for {round(wait,2)} seconds ...')
            time_pkg.sleep(wait)

time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
print(f"Finished at {time}")
