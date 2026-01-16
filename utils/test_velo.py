from db_functions import get_races_db, get_stages_db, get_teams_db, insert_roster_db, insert_riders_db
from web_functions import get_riders, get_stages, get_teams, get_team_stage_url, get_roster
import sqlite3
import requests
from bs4 import BeautifulSoup
from manual_inserts import print_first_rows

races = get_races_db()
#stages = get_stages_db(race)

reload_riders = True
reload_results = False

for race in races:

    #load all riders
    if reload_riders:
        riders_data = get_riders(race['url'])
        #print_first_rows(riders_data,6)
        insert_riders_db(race, riders_data)

    if reload_results:
        stages,teams = [],[]
        stages = get_stages_db(race,all_stages=True)
        teams = get_teams_db(race)
        
        for i,stage in enumerate(stages):
            for team in teams[:1]:
                print(f"\tLoaded: {race['name']} - {stage['stage_name']} - {team['team_name']}")
                print(f"race_id: {race['race_id']}, stage_id: {stage['stage_id']}, team_id: {team['team_id']}")
                roster = get_roster(race,stage,team)
                #print_first_rows(roster,5)
                insert_roster_db(race,stage,team,roster)
                break
            break
        if not len(stages): print(f'\tNo stages to process for {race['name']} ...')
