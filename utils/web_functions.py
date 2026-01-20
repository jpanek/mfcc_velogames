# web_functions.py

import requests
from bs4 import BeautifulSoup, SoupStrainer
import re
from datetime import datetime, timedelta

mfcc_league = 61627774

def parse_value(value):
    """Helper function to handle values like '-' and convert them to 0."""
    if value == '-':
        return 0
    return int(value)

def get_riders_url(base_url):
    url = base_url+"riders.php"
    return url

def get_team_stage_url(base_url, team, stage):
    # Format the URL with the provided parameters
    url = f"{base_url}teamroster.php?tid={team}&ga=13&st={stage}"
    return url

def get_stage_url(base_url,league,stage):
    url = f"{base_url}leaguescores.php?league={mfcc_league}&ga=13&st={stage}"
    return url

def get_team_url(base_url):
    url = f"{base_url}leaguescores.php?league={mfcc_league}"
    return url

def get_stages(race):
    # Send a GET request to fetch the HTML page
    league_url = race['url'] + "races.php"
    response = requests.get(league_url)
    response.raise_for_status()

    # Parse the page with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    stages = []

    if race['name'] == 'Sixies-superclasico':
        # Find the table containing the race data
        table = soup.find('table', {'width': '100%'})
        rows = table.find_all('tr')[1:]  # Skip the header row

        # Iterate through each row and extract the stage details
        for row in rows:
            row_html = str(row)

            # Manually fix the malformed row by adding a closing </td> for the first column
            row_html = re.sub(r'<td>(\d+)(?=\s*<td>)', r'<td>\1</td>', row_html)

            # Parse the fixed HTML row
            fixed_row = BeautifulSoup(row_html, 'html.parser')
            cols = fixed_row.find_all('td')

            if len(cols) >= 4:
                # Extract and clean the stage data
                stage_number = int(cols[0].text.strip())  # Stage number (1st column)
                stage_date = cols[1].text.strip()  # Deadline (2nd column)
                stage_name = cols[2].text.strip()  # Race name (3rd column)

                # Append the stage details to the list
                stages.append({
                    'stage': stage_number,
                    'name': stage_name,
                    'date': stage_date,
                })
    else:
        # This should run for stage races ... but needs to check:
        table = soup.find('table', class_='responsive')
        
        if table:
            rows = table.find_all('tr')[1:]  # Skip header
            today = datetime.strptime(race['start_date'], "%Y-%m-%d")

            for i, row in enumerate(rows, start=1):
                cols = row.find_all('td')
                if len(cols) >= 2:
                    stages.append({
                        'stage': i,  # Sequential stage number
                        'name': cols[0].text.strip(),  # Route name
                        'date': (today + timedelta(days=i-1)).strftime("%Y-%m-%d"),  # Incrementing date
                    })
            #For stage races append End of Tour Stage for Calssification:
            stages.append({
                'stage': 22,
                'name': 'End of Tour',
                'date': (today + timedelta(days=i-1)).strftime("%Y-%m-%d"),
            })
    return stages

def get_teams(race):
    url = get_team_url(race['url'])
    print(url)

    response = requests.get(url)
    response.raise_for_status()
    
    # Parse the page with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    teams = []
    
    # Find all the <li> elements under the div with id="users"
    user_list = soup.find('div', {'id': 'users'}).find_all('li')
    
    for user_item in user_list:
        # Extract team score (from <p class="born"><b>points</b></p>)
        team_score = int(user_item.find('p', class_='born').find('b').text.strip().split()[0])

        # Extract team ID and name (from <a href="teamroster.php?tid=XXXXX">Team Name</a>)
        team_link = user_item.find('a', href=True)
        team_id = team_link['href'].split('=')[1]
        team_name = team_link.text.strip()

        # Extract team manager name (from <p class="born">Manager Name</p>)
        team_manager = user_item.find_all('p', class_='born')[-1].text.strip()

        # Add the parsed team to the teams list
        teams.append({
            'team_code': team_id,
            'team_name': team_name,
            'team_score': team_score,
            'team_manager': team_manager
        })

    return teams

def get_roster(race, stage, team, session=None):
    url = get_team_stage_url(race['url'], team['team_code'], stage['stage_number'])
    roster = []
    print(url)

    # if session if available use it, otherwise requests (standalone)
    fetcher = session if session else requests

    # Send the GET request and parse the page
    response = fetcher.get(url)
    response.raise_for_status()

    only_table = SoupStrainer('table', {'class': 'responsive'})
    soup = BeautifulSoup(response.text, 'lxml', parse_only=only_table)

    # Get all rows (including the header)
    rows = soup.find_all('tr')

    # Iterate through each row and fix any malformed rows
    for i,row in enumerate(rows):

        row_html = str(row)

        # Manually fix the malformed row if the <tr> is missing the <td> tag for some rows
        row_html = re.sub(r'<td>(\d+)(?=\s*<td>)', r'<td>\1</td>', row_html)

        # Parse the fixed HTML row
        fixed_row = BeautifulSoup(row_html, 'html.parser')
        
        cols = fixed_row.find_all('td')

        if len(cols)>0 and cols[0].text.strip() == 'Hidden Until Race Start':
            #stop the loop if riders are not pubslished yet
            roster = None
            return roster

        if race['name'] == 'Sixies-superclasico':
            # Proceed if the row has enough columns
            if len(cols) >= 8:
                # Extract data from the table columns
                rider = cols[0].text.strip()  # 1st column: Rider name
                rider_link = cols[0].find("a")["href"]
                rider_code = rider_link.split("=")[-1]
                team_name = cols[1].text.strip()  # 2nd column: Team name
                cost = int(parse_value(cols[2].text.strip()))  # 3rd column: Cost
                finish = parse_value(cols[4].text.strip())  # 5th column: Finish
                break_points = parse_value(cols[5].text.strip())  # 6th column: Breaks
                assist = parse_value(cols[6].text.strip())  # 7th column: Assists
                total = int(parse_value(cols[7].text.strip()))  # 8th column: Total

                # Append parsed data to the roster list
                roster.append({
                    'rider_code': rider_code,
                    'rider': rider,
                    'team': team_name,
                    'cost': cost,
                    'finish': finish,
                    'break_points': break_points,
                    'assist': assist,
                    'total': total
                })
        else:
            if len(cols) >= 8:
                # Extract data from the table columns
                rider = cols[0].text.strip()  # 1st column: Rider name
                rider_link = cols[0].find("a")["href"]
                rider_code = rider_link.split("=")[-1]
                team_name = cols[1].text.strip()  # 2nd column: Team name
                cost = int(parse_value(cols[2].text.strip()))  # 3rd column: Cost
                stg = parse_value(cols[4].text.strip())  # 5th column: Finish
                gc = parse_value(cols[5].text.strip())  # 6th column: Breaks
                assist = parse_value(cols[11].text.strip())  # 7th column: Assists
                total = int(parse_value(cols[12].text.strip()))  # 8th column: Total

                # Append parsed data to the roster list
                roster.append({
                    'rider_code': rider_code,
                    'rider': rider,
                    'team': team_name,
                    'cost': cost,
                    'stage': stg,
                    'gc': gc,
                    'assist': assist,
                    'total': total
                })

    return roster

def get_riders(url):
    url = url+"riders.php"
    print(url)
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    # Locate the table
    table = soup.find('table', class_='tablesorter custom-popup')

    if not table:
        raise ValueError("Table not found on page.")

    # Extract column positions dynamically
    headers = [th.get_text(strip=True).lower() for th in table.find_all('th')]
    
    # Define the required columns and find their indexes
    column_map = {  
        "rider": None,  
        "team": None,  
        "cost": None,  
        "points": None  
    }

    for key in column_map:
        for i, header in enumerate(headers):
            if key in header:
                column_map[key] = i
                break

    # Ensure all required columns exist
    if None in column_map.values():
        raise ValueError("Some required columns are missing in the table.")

    # Extract data
    data = []
    for i,row in enumerate(table.find_all('tr')[1:]):  # Skip header row
        cols = row.find_all('td')
        if len(cols) < max(column_map.values()) + 1:
            continue  # Skip incomplete rows

        rider_name = cols[column_map["rider"]].get_text(strip=True)
        team = cols[column_map["team"]].get_text(strip=True)
        cost = cols[column_map["cost"]].get_text(strip=True)
        points = cols[column_map["points"]].get_text(strip=True)
        rider_link = cols[0].find("a")["href"]
        rider_code = rider_link.split("=")[-1]

        data.append({
            "rider": rider_name,
            "team": team,
            "cost": cost,
            "points": points,
            "rider_code": rider_code
        })

    return data



