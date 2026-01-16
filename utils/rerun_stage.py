from db_functions import get_races_db, get_stages_db, get_teams_db, insert_roster_db, insert_riders_db
from web_functions import get_riders, get_stages, get_teams, get_team_stage_url, get_roster

# ---------------------------------------------------------------------
# Configure the stage where results need to be re-run
race_name = 'Sixies-superclasico'
stage_id = 11 #RVV
reload_results = True
# ---------------------------------------------------------------------

races = get_races_db(race_name=race_name)
for race in races:

    if reload_results:
        stages,teams = [],[]
        stages = get_stages_db(race,stage_id=stage_id)
        teams = get_teams_db(race)
        
        for i,stage in enumerate(stages):
            for team in teams:
                print(f"\tLoaded: {race['name']} - {stage['stage_name']} - {team['team_name']}")
                roster = get_roster(race,stage,team)
                insert_roster_db(race,stage,team,roster)
        if not len(stages): print(f'\tNo stages to process for {race['name']} ...')
