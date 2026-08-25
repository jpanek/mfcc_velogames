# run_velo.py

from db_functions import get_races_db, get_stages_db, get_teams_db, get_rosters_db, get_rider_stage_db, propagate_roster_db, get_roster_db
from db_functions import insert_riders_db, insert_stages_db, insert_teams_db, insert_roster_db, insert_stage_points_db
from web_functions import get_riders, get_stages, get_teams, get_roster, get_rider_stage
from email_functions import send_email_stage_results
from datetime import datetime
import time as time_pkg
import random
import requests
import gc
from playwright.sync_api import sync_playwright

#create_tables() 
reload_riders = False #Only run when new race is added
reload_stages = False #Only run when new race is added
reload_teams = False #Only run when new race is added and teams submitted
load_results = True

reload_results = False #make true if you want to force results re-run 
reload_rosters = False

print(f"--------------------------------------------------------------------------")


races = get_races_db(current_flag=True)
#races = get_races_db(race_name='Itzulia', current_year=True)

for race in races:

    time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Working on race: {race['name']} started at {time_now}")

    #load all riders
    if reload_riders:
        with sync_playwright() as p:
            #browser = p.chromium.launch(headless=False)
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            riders_data = get_riders(race,page=page)
            insert_riders_db(race, riders_data)
            print(f'\t\t Loaded {len(riders_data)} riders')

    if reload_stages:
        #load all stages for a race
        with sync_playwright() as p:
            #browser = p.chromium.launch(headless=False)
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            stages = get_stages(race, page=page)
            insert_stages_db(race, stages)

    if reload_teams:
        #load teams for a race
        with sync_playwright() as p:
            #browser = p.chromium.launch(headless=False)
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            teams = get_teams(race, page=page)
            insert_teams_db(race,teams)

    if load_results:
        
        stages = get_stages_db(race)
        #stages = get_stages_db(race, all_stages=False, stage_id=1199)
        #stages = get_stages_db(race, all_stages=True)

        if not stages:
            # no need to run this, just close it
            print(f"\tNo stages to process for {race['name']} ...")
            continue

        #Stages to work on, lets continue:
        teams = get_teams_db(race)

        with sync_playwright() as p:
            #browser = p.chromium.launch(headless=True)
            browser = p.chromium.launch(headless=False,channel="chromium")
            page = browser.new_page()

            #load roasters and results:
            for i,stage in enumerate(stages):
                print(f"\tWorking on Stage: {stage['stage_number']} - {stage['stage_name']}")

                rosters = get_rosters_db(race, stage) 
                stage_points = get_rider_stage_db(race,stage)

                #if 1:
                if len(rosters)==0 or reload_rosters:
                    # ------------------------------------------------------------------------------
                    #CASE C) Rosters are not known for a stage, load them first
                    print(f"\t\t ** Rosters initial load started ...")
                    for k,team in enumerate(teams):
                        
                        roster_db = get_roster_db(race, stage, team)
                        if len(roster_db)==0 or reload_rosters:
                            # SLEEP jitter
                            wait = random.uniform(2, 4)
                            if k % 4 == 0:
                                wait += random.uniform(2,8)
                            print(f'\t\t Waiting for {round(wait,2)} seconds ...')
                            time_pkg.sleep(wait)

                            print(f"\t\tLoading teams: Team No.{k+1}: {race['name']} - {stage['stage_name']} - {team['team_name']}")
                            
                            roster = get_roster(race,stage,team, page=page)

                            if roster is None:
                                print('\t\t No rosters are published yet')
                            else:
                                #1) Save the scrapped roster to DB
                                insert_roster_db(race,stage,team,roster)
                                print('\t\t Rosters loaded ....')

                                #2) Propagate the rosters to other stages (if eligbile)
                                if race['name'] != 'Sixies-superclasico':
                                    propagate_roster_db(race['race_id'],team['team_id'],stage['stage_id'])

                            del roster
                        else:
                            print('\t\t Rosters already in DWH ....')

                        gc.collect()
                    # ------------------------------------------------------------------------------
                elif len(stage_points)==0 or reload_results:
                    # ------------------------------------------------------------------------------
                    #CASE B) Rosters are already loaded in DB, only need to refresh the results 
                    print(f"\t\t ** Rosters are already loaded => Only refreshing the results ...")

                    # SLEEP jitter
                    wait = random.uniform(2, 6)
                    print(f'\t\t Waiting for {round(wait,2)} seconds ...')
                    time_pkg.sleep(wait)

                    riders_data = get_rider_stage(race=race, stage=stage, page=page)

                    insert_stage_points_db(race=race, stage=stage, riders_data=riders_data)

                    if len(riders_data):
                        #here send email with information about results being loaded:
                        #pass
                        send_email_stage_results(race, stage)
                    # ------------------------------------------------------------------------------
                else:                   
                    # ------------------------------------------------------------------------------
                    # CASE A) Results for the stage are in place, no need to refresh anything
                    print(f"\t\t ** Results are already loaded => Skipping refresh ...")
                    #send_email_stage_results(race, stage)
                    # ------------------------------------------------------------------------------

time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
print(f"\nFinished at {time_now}")

