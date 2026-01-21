# web_functions.py

import requests
from bs4 import BeautifulSoup, SoupStrainer
import re
from datetime import datetime, timedelta
import sqlite3, os, sys
from db_functions import get_races_db, get_stages_db, get_db_path, get_teams_db, insert_roster_db
from web_functions import get_roster
mfcc_league = 61627774


race_set ={
    "name":"Tour Down Under",
    "year":"2026",
    "url":"https://www.velogames.com/tour-down-under/2026/",
    "start_date":"2026-01-20",
    "end_date":"2026-01-25"
}

races = get_races_db(race_set['name'])


def get_riders_stage_url(base_url, stage):
    # Format the URL with the provided parameters
    stage_number = stage['stage_number']
    url = f"{base_url}ridescore.php?&ga=13&st={stage_number}"
    return url

def get_rider_stage(race, stage):

    url = get_riders_stage_url(race['url'], stage)
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    riders_data = []

    # Find all list items within the users div
    for li in soup.select('#users ul.list li'):
        # Extract Name and ID
        link = li.find('h3', class_='name').find('a')
        rider_name = link.get_text(strip=True)
        
        # Extract ID from the href using regex
        href = link.get('href', '')
        rider_id_match = re.search(r'rider=(\d+)', href)
        rider_id = rider_id_match.group(1) if rider_id_match else None
        
        # Extract Points
        # Points are in the first 'p' tag with class 'born' inside the float:right span
        points_text = li.find('span', style="float:right").find('p', class_='born').get_text(strip=True)
        rider_points = int(re.search(r'\d+', points_text).group())

        riders_data.append({
            'rider_id': rider_id,
            'rider_name': rider_name,
            'rider_points': rider_points
        })

    return riders_data


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
        
        print(f"\tLoaded rider: No {i+1} {rider_name} scored {rider_points} points")

    conn.commit()
    conn.close()

'''
for race in races:
    stages = get_stages_db(race, all_stages=True)
    for stage in stages:
        print(f"Working on {race['name']} and stage {stage['stage_name']}")

        rosters = get_rosters_db(race, stage)
        print(len(rosters))

        riders_data = get_rider_stage(race=race,stage=stage)
        #print(riders_data)
        insert_stage_points_db(race=race, stage=stage, riders_data=riders_data)
'''

'''
# fix rosters for a stage historically
races = get_races_db('Spain')
for race in races:
    stages = get_stages_db(race, stage_id=614)
    teams = get_teams_db(race)
    for stage in stages:
        for team in teams:
            roster = get_roster(race,stage,team)
            insert_roster_db(race,stage,team,roster)
'''            
