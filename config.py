# config.py

import os

#get directory of this file
basedir = os.path.abspath(os.path.dirname(__file__))

DB_PATH = os.path.join(basedir, 'velogames.db')
LOG_PATH = os.path.join(basedir,'logs','cron_log.log')

COLOR_LIST = [
    "#1F77B4",  # Blue
    "#FF7F0E",  # Orange
    "#2CA02C",  # Green
    #"#D62728",  # Red
    "#9467BD",  # Purple
    "#8C564B",  # Brown
    "#E377C2",  # Pink
    "#7F7F7F",  # Gray
    "#BCBD22",  # Yellow-Green
    "#17BECF",  # Cyan
    "#F08080",  # Light Coral
    "#FFD700",  # Gold
    "#32CD32",  # Lime Green
    "#4682B4",  # Steel Blue
    "#FF69B4",  # Hot Pink
]

class Config:
    MAIL_USERNAME = "juraj.panek@gmail.com"
    MAIL_PASSWORD = "fbcsryrswykpqyxc"
    
    RECIPIENTS = [
        'juraj.panek@gmail.com', 
        #'janieh87@gmail.com'
    ]