from db_functions import get_races_db, get_stages_db, get_teams_db
from db_functions import insert_riders_db, insert_stages_db, insert_teams_db, insert_roster_db
from web_functions import get_riders, get_stages, get_teams, get_roster
from datetime import datetime
import time as time_pkg
import random

#create_tables() 
reload_riders = False #Only run when new race is added
reload_stages = False #Only run when new race is added
reload_teams = False #Only run when new race is added and teams submitted
load_results = True

print(f"--------------------------------------------------------------------------")

races = get_races_db(current_flag=True, race_name='Sixies-superclasico')
for race in races:
    time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Working on race: {race['name']} started at {time_now}")
    
    #load all riders
    if reload_riders:
        riders_data = get_riders(race['url'])
        insert_riders_db(race, riders_data)

    if reload_stages:
        #load all stages for a race
        stages = get_stages(race)
        insert_stages_db(race, stages)

    if reload_teams:
        #load teams for a race
        teams = get_teams(race)
        insert_teams_db(race,teams)

    if load_results:
        stages,teams = [],[]
        stages = get_stages_db(race, all_stages=True)
        teams = get_teams_db(race)
        #load roasters and results:
        for i,stage in enumerate(stages):
            for team in teams:
                print(f"\tLoading: No. {i+1}: {race['name']} - {stage['stage_name']} - {team['team_name']}")
                roster = get_roster(race,stage,team)
                if roster is None:
                    print('\t\t No rosters are published yet')
                else:
                    insert_roster_db(race,stage,team,roster)
                    print('\t\t Rosters loaded ....')
                wait = random.uniform(6, 12)
                print(f'\t\t Waiting for {wait} seconds ...')
                time_pkg.sleep(wait)
        if not len(stages): print(f'\tNo stages to process for {race['name']} ...')

time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
print(f"Finished at {time_now}")