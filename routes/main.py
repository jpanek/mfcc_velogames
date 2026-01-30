from flask import Blueprint, render_template, request, json, current_app, redirect, url_for, flash
from utils.db_functions import get_data_from_db, get_pd_from_db, print_first_rows
from utils.queries import sql_stages_podium, sql_stages_chart, sql_stage_results, sql_stage_roster, sql_gc_results, sql_next_stages
from utils.queries import sql_calendar, sql_stage, sql_riders_rank, sql_rider, sql_riders_rank_all, sql_races
from utils.queries import sql_teams, sql_teams_chart, sql_team, sql_teams_overall, sql_teams_overall_year, sql_report
from utils.queries import sql_races_podium_year
from datetime import datetime
import os
import subprocess

main_bp = Blueprint('main',__name__)

""" Index route 
------------------------------------------------------------------------- """
@main_bp.route('/')
def index():
    columns, data = get_data_from_db(sql_calendar)
    columns_2, data_2 = get_data_from_db(sql_teams_overall_year)
    #columns_3, data_3 = get_data_from_db(sql_teams_overall)
    columns_3, data_3 = get_data_from_db(sql_races_podium_year)

    df = get_pd_from_db(sql_riders_rank_all)

    # Build data for Chart.js
    chart_data = []
    for _, row in df.iterrows():
        chart_data.append({
            "x": row["Cost"],
            "y": row["Points"],
            "label": row["Rider"]
        })
    chart_data=json.dumps(chart_data)

    return render_template('index.html',
                           columns=columns, 
                           data=data,
                           chart_data=chart_data,
                           columns_2 = columns_2,
                           data_2 = data_2,
                           columns_3 = columns_3,
                           data_3 = data_3
                           )

@main_bp.route('/race', methods=['GET'])
def race():
    race_id = request.args.get('race_id')
    params = (race_id,)
    columns, data = get_data_from_db(sql_stages_podium, params)
    ch_columns,ch_data = get_data_from_db(sql_stages_chart,params)
    _, races = get_data_from_db(sql_races,params)

    # Extract managers and stages
    managers = sorted(set(item['team_manager'] for item in ch_data))
    stages = sorted(set(item['stage_number'] for item in ch_data))
    
    # Initialize chart data structure
    chart_data = {manager: {stage: None for stage in stages} for manager in managers}
    
    # Fill cumulative points
    for row in ch_data:
        chart_data[row['team_manager']][row['stage_number']] = row['cum_pts']
    
    # Map stage numbers to stage names
    stage_mapping = {item['stage_number']: item['stage_name'] for item in ch_data}
    labels = [stage_mapping[stage] for stage in stages]
    
    # Prepare datasets
    datasets = []
    colors = current_app.config['COLOR_LIST']
    for index, (manager, points) in enumerate(chart_data.items()):
        dataset = {
            "label": manager,
            "data": [points[stage] for stage in stages],
            "borderColor": colors[index % len(colors)],
            "fill": False,
            "tension": 0.1
        }
        datasets.append(dataset)

    race_name = races[0]['name']
    #race_name = ch_data[0]['race_name']
    title = f"{race_name} leaderboard"
    return render_template('race.html',
                           columns=columns, 
                           data=data, 
                           title=title, 
                           labels=labels, 
                           datasets=datasets
                           )

@main_bp.route('/stage', methods=['GET'])
def stage():
    colors = current_app.config['COLOR_LIST']

    stage_id = request.args.get('stage_id', type=int)
    params = (stage_id,)
    columns, data = get_data_from_db(sql_stage_results, params)
    columns_gc, data_gc = get_data_from_db(sql_gc_results, params)
    _, data_roster = get_data_from_db(sql_stage_roster, params)
    _, stages = get_data_from_db(sql_next_stages,params)
    results = data[0]['results_ready']

    race_id = stages[0]['race_id']
    # Find the current stage's position in the list of stages
    current_stage = next((stage for stage in stages if stage['stage_id'] == int(stage_id)), None)
    if current_stage:
        current_index = stages.index(current_stage)
        prev_stage = stages[current_index - 1] if current_index > 0 else None
        next_stage = stages[current_index + 1] if current_index < len(stages) - 1 else None
    else:
        prev_stage = next_stage = None

    # Process Data
    managers = sorted(set(row["team_manager"] for row in data_roster))  # X-axis labels
    #riders = sorted(set(row["rider"] for row in data_roster))  # Unique riders
    riders = sorted(set(row["rider"] for row in data_roster if row["rider"] is not None))

    chart_data = {manager: {rider: 0 for rider in riders} for manager in managers}
    table_data = {manager: [] for manager in managers}

    roster = data_roster[0]['rider']
    datasets = []
    rider_ownership_map = {}
    ownership_list = []

    if roster is not None:
    
        for row in data_roster:
            chart_data[row["team_manager"]][row["rider"]] = row["total"]
            name_parts = row['rider'].split()
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else name_parts[0]
            rider = f"{last_name} ({row['cost']} - {row['total']})"
            table_data[row["team_manager"]].append((rider, row["cost"]))

            r_name = row['rider']
            if r_name not in rider_ownership_map:
                rider_ownership_map[r_name] = {
                    'name': r_name,
                    'count': 0,
                    'managers': [],
                    'total_points': row['total'] # Optional: if you want to sort by points
                }
            
            rider_ownership_map[r_name]['count'] += 1
            rider_ownership_map[r_name]['managers'].append(row["team_manager"])

        # 3. Convert to a list and Sort (Example: by Count descending, then Name)
        ownership_list = sorted(
            rider_ownership_map.values(), 
            key=lambda x: (x['count'], x['total_points']), 
            reverse=True
        )
        
        # Sort riders within each manager's list by total points (descending)
        for manager in table_data:
            table_data[manager].sort(key=lambda x: x[1], reverse=True)

        # Remove total values, keeping only rider names for table display
        for manager in table_data:
            table_data[manager] = [r[0] for r in table_data[manager]]

        
        for i, rider in enumerate(riders):
            dataset = {
                "label": rider,
                "data": [chart_data[manager][rider] for manager in managers],
                "backgroundColor": colors[i % len(colors)],
            }
            datasets.append(dataset)
    
    chart_labels = managers  # X-axis labels
    chart_datasets = datasets

    if len(data):
        race_name = data[0]['race_name']
        stage_name = data[0]['stage_name']
        stage_date = data[0]['stage_date']
        title = f"{race_name} - {stage_name} - {stage_date}"
    else:
        columns, data = get_data_from_db(sql_stage, params)
        race_name = data[0]['race_name']
        stage_name = data[0]['stage_name']
        stage_date = data[0]['stage_date']
        title = f"{race_name} - {stage_name} - {stage_date}"
        message = "Data not available yet"
        return render_template('stage_not_ready.html',title=title, message=message)

    date_obj = datetime.strptime(stage_date, '%Y-%m-%d')
    # Format it as '24 Mar'
    #formatted_date = date_obj.strftime('%d %b')

    return render_template('stage.html',
                           columns=columns, 
                           data=data, 
                           columns_gc=columns_gc,
                           data_gc=data_gc,
                           title=title,
                           race_name=race_name,
                           stage_name=stage_name,
                           stage_date=stage_date,
                           chart_labels=chart_labels,
                           chart_datasets=chart_datasets,
                           table_data=table_data,
                           chart_data=chart_data,
                           results=results,
                           roster=roster,
                           prev_stage=prev_stage, 
                           next_stage=next_stage,
                           ownership_list = ownership_list,
                           race_id = race_id
                           )

@main_bp.route('/riders', methods=['GET'])
def riders():
    race_id = request.args.get('race_id')
    params = (race_id,)
    columns, data = get_data_from_db(sql_riders_rank,params)

    if not data:
        return render_template('error.html', message="Data not available for this race.")

    race = data[0]['race_name']
    title = f"Team riders for {race}"

    df = get_pd_from_db(sql_riders_rank, params)

    # Build data for Chart.js
    chart_data = []
    for _, row in df.iterrows():
        chart_data.append({
            "x": row["Cost"],
            "y": row["Points"],
            "label": row["Rider"]
        })
    chart_data=json.dumps(chart_data)

    return render_template('riders.html',
                           title=title,
                           columns=columns,
                           data=data,
                           chart_data=chart_data
                           )

@main_bp.route('/rider', methods=['GET'])
def rider():
    race_id = request.args.get('race_id')
    rider_code = request.args.get('rider_code')
    params = (race_id, rider_code,)

    columns, data = get_data_from_db(sql_rider,params)

    print(data)
    rider = data[0]['rider']
    title = f"Races by {rider}"

    return render_template('rider.html',
                    title=title,
                    columns=columns,
                    data=data
                    )

@main_bp.route('/scatter')
def scatter():
    race_id = 1
    params = (race_id,)
    df = get_pd_from_db(sql_riders_rank, params)

    # Build data for Chart.js
    chart_data = []
    for _, row in df.iterrows():
        chart_data.append({
            "x": row["Cost"],
            "y": row["Points"],
            "label": row["Rider"]
        })

    return render_template("scatter.html", chart_data=json.dumps(chart_data))

@main_bp.route('/log')
def view_log():
    log_path = current_app.config.get('LOG_PATH')
    content = ""
    if log_path and os.path.exists(log_path):
        with open(log_path, 'r') as f:
            lines = f.readlines()
            content = "".join(reversed(lines[-100:]))
    
    return render_template('log_viewer.html', content=content)

@main_bp.route('/teams', methods=['GET'])
def teams():
    colors = current_app.config['COLOR_LIST']
    race_id = request.args.get('race_id')
    params = (race_id,)
    columns, data = get_data_from_db(sql_teams,params)

    if not data:
        return render_template('error.html', message="Data not available for this race.")

    ch_columns,ch_data = get_data_from_db(sql_teams_chart,params)
    _, races = get_data_from_db(sql_races,params)

    # Extract managers and stages
    managers = sorted(set(item['team_manager'] for item in ch_data))
    stages = sorted(set(item['stage_number'] for item in ch_data))

    # Initialize chart data structure
    chart_data = {manager: {stage: None for stage in stages} for manager in managers}
    
    # Fill cumulative points
    for row in ch_data:
        chart_data[row['team_manager']][row['stage_number']] = row['cum_pts']
    
    # Map stage numbers to stage names
    stage_mapping = {item['stage_number']: item['stage_name'] for item in ch_data}
    labels = [stage_mapping[stage] for stage in stages]
    
    # Prepare datasets
    datasets = []
    for index, (manager, points) in enumerate(chart_data.items()):
        dataset = {
            "label": manager,
            "data": [points[stage] for stage in stages],
            "borderColor": colors[index % len(colors)],
            "fill": False,
            "tension": 0.1
        }
        datasets.append(dataset)
    
    race = data[0]['race_name']
    title = f"Teams stats for {race}"


    return render_template('teams.html',
                           title=title,
                           columns=columns,
                           data=data,
                            labels=labels, 
                           datasets=datasets
                           )

@main_bp.route('/team', methods=['GET'])
def team():
    #race_id = request.args.get('race_id')
    team_id = request.args.get('team_id')
    print(team_id)
    params = (team_id,)

    columns, data = get_data_from_db(sql_team,params)

    
    race_name = data[0]['race_name']
    team_name = data[0]['team_name']
    title = f"{race_name} results of {team_name}"
    

    return render_template('team.html',
                    title=title,
                    columns=columns,
                    data=data
                    )

@main_bp.route('/report', methods=['GET'])
def ad_hoc():

    columns, data = get_data_from_db(sql_report)

    title = f"Category 3 Stages"
    subtitle = f"Most stage wins"
    

    return render_template('report.html',
                    title=title,
                    subtitle =subtitle,
                    columns=columns,
                    data=data
                    )

@main_bp.route('/run-worker', methods=['POST'])
def run_worker():
    log_path = current_app.config.get('LOG_PATH')
    project_root = os.path.dirname(os.path.dirname(log_path))
    
    script_path = os.path.join(project_root, 'utils', 'run_velo.py')
    python_executable = os.path.join(project_root, 'venv', 'bin', 'python3')

    try:
        with open(log_path, "a") as log_file:
            log_file.write(f"\n*** [Manual Run Started via Web] ***\n")
            subprocess.Popen(
                [python_executable, "-u", script_path],
                stdout=log_file,
                stderr=log_file,
                cwd=project_root
            )
    except Exception as e:
        # We'll just print to the console since we aren't using flash
        print(f"Error starting background worker: {e}")

    # Just redirect back to the log page immediately
    return redirect(url_for('main.view_log'))

# Error handlers ---------------------------------------------------
@main_bp.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@main_bp.app_errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 404


