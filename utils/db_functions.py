# db_functions.py

import sqlite3, os, sys
import pandas as pd
from flask import current_app

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    import config
except ImportError:
    # This handles edge cases where the path might still be tricky
    from .. import config

def get_db_path():
    try:
        # This works when the website is running
        return current_app.config['DB_PATH']
    except (RuntimeError, AttributeError):
        # This works for your manual_inserts.py and cron jobs
        return config.DB_PATH

def create_tables():
    # Connect to the database (it will create 'velogames.db' if it doesn't exist)
    #conn = sqlite3.connect(db_path)
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()

    # Drop the tables if they already exist
    #c.execute('DROP TABLE IF EXISTS riders')
    #c.execute('DROP TABLE IF EXISTS races')
    #c.execute('DROP TABLE IF EXISTS stages')

    # Create races table with the 'year' column
    c.execute('''
        CREATE TABLE races (
            race_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL,
            year       INTEGER NOT NULL,
            url        TEXT    NOT NULL,
            start_date TEXT,
            UNIQUE (
                name,
                year
            )
        );
    ''')

    # Create riders table
    c.execute('''
        CREATE TABLE IF NOT EXISTS riders (
            rider_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            team TEXT NOT NULL,
            race_id INTEGER,
            points INTEGER,
            cost    integer,
            UNIQUE(name, race_id),  -- Ensure the same rider isn't added multiple times for the same race
            FOREIGN KEY (race_id) REFERENCES races(race_id) ON DELETE CASCADE
        )
    ''')

    # Create stages table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS stages (
            stage_id INTEGER PRIMARY KEY AUTOINCREMENT,
            stage_name TEXT NOT NULL,
            stage_number INTEGER NOT NULL,
            race_id INTEGER,
            FOREIGN KEY (race_id) REFERENCES races(race_id) ON DELETE CASCADE,
            UNIQUE(stage_number, race_id)
        )
    ''')

    conn.commit()
    conn.close()

def get_races_db(race_name=None, current_flag=False):
    """Fetch races from the database. Optionally filter by race name and/or current date."""
    try:
        #conn = sqlite3.connect(db_path)
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        sql = "SELECT * FROM races WHERE 1=1"
        params = ()

        if race_name:
            sql += " AND name = ?"
            params += (race_name,)

        if current_flag:
            sql += " AND date('now') BETWEEN date(start_date, '-2 days') AND date(end_date, '+2 days')"

        c.execute(sql, params)
        return c.fetchall()

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None

    finally:
        conn.close()

def get_stages_db(race,all_stages=False, stage_id=None):
    #conn = sqlite3.connect(db_path)
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    race_id = race['race_id']

    if all_stages:
        sql = """
        select * from stages 
        where 0=0
        and   race_id = ?
        --and   date(stage_date) <= date('now')
        """
        params = (race_id,)
    elif stage_id is not None:
        sql = """
        select * from stages 
        where 0=0
        and   race_id = ?
        and   stage_id = ?
        --and   stage_date <= date('now')
        """
        params = (race_id,stage_id,)
    else:
        sql = """
        select * from stages 
        where 0=0
        and   race_id = ?
        --and   race_id = 91
        --and stage_number = 3
        and   date(stage_date) >= date('now','-1 day') and date(stage_date) <= date('now')
        and   date(stage_date) = date('now','-0 day')
        --and   0=1
        """
        params = (race_id,)
    
    c.execute(sql, params)

    stages = c.fetchall()
    conn.close()
    return stages
    
def get_teams_db(race):
    #conn = sqlite3.connect(db_path)
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    race_id = race['race_id']

    sql = """
    select * from teams 
    where 0=0
    and   race_id = ?
    --and   team_id = 600 -- to delete
    """
    c.execute(sql, (race_id,))

    stages = c.fetchall()
    conn.close()
    return stages

def get_rosters_db(race,stage):
    #conn = sqlite3.connect(db_path)
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    race_id = race['race_id']
    stage_id = stage['stage_id']

    sql = """
    select * from rosters 
    where race_id = ?
    and   stage_id = ?
    """
    c.execute(sql, (race_id, stage_id,))

    rosters = c.fetchall()
    conn.close()
    return rosters

def insert_riders_db(race, riders_data):
    #conn = sqlite3.connect(db_path)
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    race_id = race['race_id']

    # Prepare the data for bulk insert
    riders_to_insert = [
        (rider['rider'], rider['team'], race_id, rider['points'], rider['cost'], rider['rider_code'])
        for rider in riders_data
    ]

    # Insert riders into the riders table in bulk
    c.executemany('''
        INSERT OR replace INTO riders (name, team, race_id, points, cost, rider_code)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', riders_to_insert)

    conn.commit()
    conn.close()

def insert_teams_db(race, teams):
    race_id = race['race_id']
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()

    for i, team in enumerate(teams):
        team_name = team['team_name']
        team_code = team['team_code']
        team_manager = team['team_manager']
        team_score = team.get('team_score', 0)

        # First, try to insert if it doesn't exist
        c.execute("""
            INSERT OR IGNORE INTO teams (team_name, team_code, team_manager, team_score, race_id)
            VALUES (?, ?, ?, ?, ?)
        """, (team_name, team_code, team_manager, team_score, race_id))

        # Then, update if already exists
        c.execute("""
            UPDATE teams
            SET team_name = ?, team_manager = ?, team_score = ?
            WHERE team_code = ? AND race_id = ?
        """, (team_name, team_manager, team_score, team_code, race_id))

    print(f"\tProcessed {i+1} teams to DB")
    conn.commit()
    conn.close()

def insert_stages_db(race, stages):
    race_id = race['race_id']
    #conn = sqlite3.connect(db_path)
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()

    for i, stage in enumerate(stages):
        stage_number = stage['stage']
        stage_name = stage['name']
        stage_date = stage['date']

        # Try insert
        c.execute('''
            INSERT OR IGNORE INTO stages (stage_name, stage_number, stage_date, race_id)
            VALUES (?, ?, ?, ?)
        ''', (stage_name, stage_number, stage_date, race_id))

        # Then update
        c.execute('''
            UPDATE stages
            SET stage_name = ?, stage_date = ?
            WHERE race_id = ? AND stage_number = ?
        ''', (stage_name, stage_date, race_id, stage_number))

    print(f"Processed {i+1} stages to DB")
    conn.commit()
    conn.close()

def insert_roster_db(race, stage, team, roster):
    race_id = race['race_id']
    stage_id = stage['stage_id']
    team_id = team['team_id']
    #conn = sqlite3.connect(db_path)
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if race['name'] == 'Sixies-superclasico':
        # Insert the roster data into the rosters table
        for rider_data in roster:
            c.execute("""
                INSERT or replace INTO rosters (stage_id, race_id, team_id, rider, team, cost, finish, break_points, assist, total, rider_code)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                stage_id,
                race_id,
                team_id,
                rider_data['rider'],
                rider_data['team'],
                rider_data['cost'],
                rider_data['finish'],
                rider_data['break_points'],
                rider_data['assist'],
                rider_data['total'],
                rider_data['rider_code']
            ))
    else:
        # Insert the roster data into the rosters table
        for rider_data in roster:
            c.execute("""
                INSERT or replace INTO rosters (stage_id, race_id, team_id, rider, team, cost, stage, gc, assist, total, rider_code)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                stage_id,
                race_id,
                team_id,
                rider_data['rider'],
                rider_data['team'],
                rider_data['cost'],
                rider_data['stage'],
                rider_data['gc'],
                rider_data['assist'],
                rider_data['total'],
                rider_data['rider_code']
            ))

    conn.commit()
    conn.close()

def insert_stage_points_db(race, stage, riders_data):
    race_id = race['race_id']
    stage_id = stage['stage_id']
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()

    for i, rider_data in enumerate(riders_data):
        rider_code = rider_data['rider_id']
        rider_name = rider_data['rider_name']
        rider_points = rider_data['rider_points']

        # 1. Insert if new
        c.execute("""
            INSERT OR IGNORE INTO stage_points (race_id, stage_id, rider_code, rider_name, points)
            VALUES (?, ?, ?, ?, ?)
        """, (race_id, stage_id, rider_code, rider_name, rider_points))

        # 2. Update if exists (Trigger handles updated_date automatically)
        c.execute("""
            UPDATE stage_points
            SET rider_name = ?, points = ?
            WHERE race_id = ? AND stage_id = ? AND rider_code = ?
        """, (rider_name, rider_points, race_id, stage_id, rider_code))
        
        #print(f"\tLoaded rider: No {i+1} {rider_name} scored {rider_points} points")

    print(f"\tLoaded points for {i+1} riders.")

    conn.commit()
    conn.close()

def get_data_from_db(query, params=None):
    # Default to empty tuple if no parameters are provided
    if params is None:
        params = ()
    
    # Connect to the SQLite database
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Execute the query with the parameters
    cursor.execute(query, params)
    column_names = [description[0] for description in cursor.description]
    
    # Fetch all rows from the query
    rows = cursor.fetchall()
    
    # Close the database connection
    conn.close()
    
    return column_names,rows
 
def get_pd_from_db(query, params=None):
    if params is None:
        params = ()
    
    conn = sqlite3.connect(get_db_path())
    df = pd.read_sql_query(query,conn,params=params)
    conn.close

    return df

def print_first_rows(data,n=30):
    for row in data[:n]:
        if isinstance(row, sqlite3.Row):
            print(dict(row))  # Print as dictionary
        else:
            print(row)  # Print normally