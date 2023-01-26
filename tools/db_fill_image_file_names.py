#!/usr/bin/env python3
import logging
import sys, os
from pathlib import Path

os.environ['RPW_SCRIPT_BASE'] = str(Path(os.getcwd()).parent)
os.environ['RPW_LOG_PATH'] = str(Path(os.getcwd()).parent / 'logs/')
os.environ['RPW_LOG_LEVEL'] = 'DEBUG'
sys.path.insert(0, os.environ['HOME'] + '/RarePepeWorld/')  # rpw path

from rpw.DataConnectors import DBConnector

"""
Initiate image file names for each pepe in the database.
Store the image file names in the database.  Since various pepe's use different image file types.
"""

db_connector = DBConnector()

for pepe_file in Path('../rpw/static/pepes/images').iterdir():
    file_name = pepe_file.name
    pepe_name = file_name.split('.')[:-1][0]
    query = f"UPDATE assets SET image_file_name=\'{file_name}\' WHERE asset=\'{pepe_name}\'"
    print(query)
    db_connector.execute(query)
