# run_velo.py

from db_functions import get_races_db, get_stages_db, get_teams_db, get_rosters_db, get_rider_stage_db, propagate_roster_db
from db_functions import insert_riders_db, insert_stages_db, insert_teams_db, insert_roster_db, insert_stage_points_db
from web_functions import get_riders, get_stages, get_teams, get_roster, get_rider_stage
from email_functions import send_email_stage_results
from datetime import datetime
import time as time_pkg
import random
import requests
import gc

#create_tables() 
reload_riders = False #Only run when new race is added
reload_stages = False #Only run when new race is added
reload_teams = False #Only run when new race is added and teams submitted
load_results = True

reload_results = False
reload_rosters = False

print(f"--------------------------------------------------------------------------")

#races = get_races_db(current_flag=True, race_name='Itzulia')
races = get_races_db(current_flag=True)

for race in races:

    # 1 session for one race
    with requests.Session() as session:

        time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"Working on race: {race['name']} started at {time_now}")
        
        #load all riders
        if reload_riders:
            riders_data = get_riders(race['url'],session=session)
            insert_riders_db(race, riders_data)
            print(f'\t\t Loaded {len(riders_data)} riders')

        if reload_stages:
            #load all stages for a race
            stages = get_stages(race, session=session)
            insert_stages_db(race, stages)

        if reload_teams:
            #load teams for a race
            teams = get_teams(race, session=session)
            insert_teams_db(race,teams)

        if load_results:

            stages,teams = [],[]
            
            stages = get_stages_db(race)
            #stages = get_stages_db(race, all_stages=False, stage_id=698)
            
            teams = get_teams_db(race)
            #load roasters and results:
            for i,stage in enumerate(stages):
                print(f"\tWorking on Stage: {stage['stage_number']} - {stage['stage_name']}")

                rosters = get_rosters_db(race, stage) 
                stage_points = get_rider_stage_db(race,stage)

                if len(rosters)==0 or reload_rosters:
                    # ------------------------------------------------------------------------------
                    #CASE C) Rosters are not known for a stage, load them first
                    print(f"\t\t ** Rosters initial load started ...")
                    for k,team in enumerate(teams):
                        
                        # SLEEP jitter
                        wait = random.uniform(4, 6)
                        if k % 4 == 0:
                            wait += random.uniform(5,15)
                        print(f'\t\t Waiting for {round(wait,2)} seconds ...')
                        time_pkg.sleep(wait)

                        print(f"\t\tLoading teams: Team No.{k+1}: {race['name']} - {stage['stage_name']} - {team['team_name']}")
                        
                        roster = get_roster(race,stage,team, session=session)

                        if roster is None:
                            print('\t\t No rosters are published yet')
                        else:
                            #1) Save the scrapped roster to DB
                            insert_roster_db(race,stage,team,roster)
                            print('\t\t Rosters loaded ....')

                            #2) Propagate the rosters to other stages (if eligbile)
                            propagate_roster_db(race['race_id'],team['team_id'],stage['stage_id'])

                        del roster
                        gc.collect()
                    # ------------------------------------------------------------------------------
                elif len(stage_points)==0 or reload_results:
                    # ------------------------------------------------------------------------------
                    #CASE B) Rosters are already loaded in DB, only need to refresh the results 
                    print(f"\t\t ** Rosters are already loaded => Only refreshing the results ...")

                    # SLEEP jitter
                    wait = random.uniform(5, 40)
                    print(f'\t\t Waiting for {round(wait,2)} seconds ...')
                    time_pkg.sleep(wait)

                    riders_data = get_rider_stage(race=race, stage=stage, session=session)
                    insert_stage_points_db(race=race, stage=stage, riders_data=riders_data)

                    if len(riders_data):
                        #here send email with information about results being loaded:
                        send_email_stage_results(race, stage)
                    # ------------------------------------------------------------------------------
                else:                   
                    # ------------------------------------------------------------------------------
                    # CASE A) Results for the stage are in place, no need to refresh anything
                    print(f"\t\t ** Results are already loaded => Skipping refresh ...")
                    #send_email_stage_results(race, stage)
                    # ------------------------------------------------------------------------------

            if not len(stages): print(f'\tNo stages to process for {race['name']} ...')

time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
print(f"\nFinished at {time_now}")

