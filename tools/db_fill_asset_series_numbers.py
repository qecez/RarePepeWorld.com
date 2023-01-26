#!/usr/bin/env python3
import logging
import sys, os
from pathlib import Path
from pprint import pformat

os.environ['RPW_SCRIPT_BASE'] = str(Path(os.getcwd()).parent)
os.environ['RPW_LOG_PATH'] = str(Path(os.getcwd()).parent / 'logs/')
os.environ['RPW_LOG_LEVEL'] = 'DEBUG'
sys.path.insert(0, os.environ['HOME'] + '/RarePepeWorld/') # rpw path

from rpw.Utils import JSONTool
from rpw.DataConnectors import DBConnector


"""
Initiate the series data for each pepe in the database.
Pulls the series data from the data file and inserts the value into the database
"""
db_connector = DBConnector()
pepe_data = JSONTool.read_json_file('../rpw/static/pepes/pepe-feed.json')
series_data = [(pepe_name, pepe_data[pepe_name]['series']) for pepe_name in pepe_data.keys()]
# print(pformat(series_data))

for series_entry in series_data:
    query = f"UPDATE assets SET series={series_entry[1]} WHERE asset='{series_entry[0]}'"
    print(query)
    db_connector.execute(query)

db_connector.commit()