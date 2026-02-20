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


def insert_race(name, year, url, start_date, end_date):
    #conn = sqlite3.connect(db_path)
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()

    # Insert a new race into the races table
    c.execute('''
        INSERT OR IGNORE INTO races (name, year, url, start_date,end_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, year, url, start_date, end_date))

    conn.commit()
    conn.close()

# Insert the races

race_set ={
    "name":"Algarve",
    "year":"2026",
    "url":"https://www.velogames.com/algarve/2026/",
    "start_date":"2026-02-18",
    "end_date":"2026-02-22"
}

insert_race(race_set['name'],race_set['year'], race_set['url'], race_set['start_date'], race_set['end_date'])

races = get_races_db(race_set['name'])


#races = get_races_db('Murcia')
races = get_races_db('Algarve')

if 1:

    for race in races:
        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"Working on race: {race['name']} started at {time}")
        
        with requests.Session() as session:

            #load all riders
            if 0:
                riders_data = get_riders(race['url'], session=session)
                insert_riders_db(race, riders_data)
                print(f'\t\t Loaded {len(riders_data)} riders')
                
                wait = random.uniform(10, 20)
                print(f'\t\t Waiting for {round(wait,2)} seconds ...')
                time_pkg.sleep(wait)

            if 0:
                #load all stages for a race
                stages = get_stages(race, session=session)
                #print_first_rows(stages,12)
                insert_stages_db(race, stages)
                #print(f'\t\t Loaded {len(stages)} stages')

                wait = random.uniform(5, 20)
                print(f'\t\t Waiting for {round(wait,2)} seconds ...')
                time_pkg.sleep(wait)

            if 1:
                #load teams for a race
                teams = get_teams(race, session=session)

                #print_first_rows(teams)
                insert_teams_db(race,teams)

                wait = random.uniform(5, 20)
                print(f'\t\t Waiting for {round(wait,2)} seconds ...')
                time_pkg.sleep(wait)

            if 1:
                stages,teams = [],[]
                #stages = get_stages_db(race,all_stages=True)
                stages = get_stages_db(race)
                teams = get_teams_db(race)
                #load roasters and results:
                for i,stage in enumerate(stages):
                    for team in teams:
                        print(f"\tLoading: {race['name']} - {stage['stage_name']} - {team['team_name']}")

                        roster_db = get_roster_db(race,stage,team)
                        if len(roster_db)==0:
                            roster = get_roster(race,stage,team, session=session)
                            if roster is None:
                                print('\t\t No rosters are published yet')
                            else:
                                insert_roster_db(race,stage,team,roster)
                                print('\t\t Rosters loaded ....')
                                propagate_roster_db(race['race_id'],team['team_id'],stage['stage_id'])
                                wait = random.uniform(15, 40)
                                print(f'\t\t Waiting for {round(wait,2)} seconds ...')
                                time_pkg.sleep(wait)
                        else:
                            print('\t\t Rosters already in DWH ....')

                if not len(stages): print(f'\tNo stages to process for {race['name']} ...')

    time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Finished at {time}")
    