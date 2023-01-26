#!/usr/bin/env python3
import sys, os
from pathlib import Path

os.environ['RPW_SCRIPT_BASE'] = str(Path(os.getcwd()).parent)
os.environ['RPW_LOG_PATH'] = str(Path(os.getcwd()).parent / 'logs/')
os.environ['RPW_LOG_LEVEL'] = 'DEBUG'

sys.path.insert(0, os.environ['HOME'] + '/RarePepeWorld/')  # Run path for rpw modules


from rpw.Utils import JSONTool
from rpw.DataConnectors import DBConnector

"""
Initiate the artist address for each people into the database.
"""

db_connector = DBConnector()

artists_file = '../rpw/static/pepes/pepe-artists.txt'
with open(artists_file, 'r') as f:
    artists_data = f.read()


table = 'assets'
column = 'source'

artists = JSONTool.parse_json(artists_data)
for pepe_name in artists.keys():
    query = f"UPDATE {table} SET {column}=\'{artists[pepe_name]}\' WHERE asset=\'{pepe_name}\'"
    print(query)
    db_connector.execute(query)

db_connector.close()
