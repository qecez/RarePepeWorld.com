#!/usr/bin/env python3
import logging
import sys, os
from pathlib import Path

os.environ['RPW_SCRIPT_BASE'] = str(Path(os.getcwd()).parent)
os.environ['RPW_LOG_PATH'] = str(Path(os.getcwd()).parent / 'logs/')
os.environ['RPW_LOG_LEVEL'] = 'DEBUG'
sys.path.insert(0, os.environ['HOME'] + '/RarePepeWorld/') # rpw path

from rpw.DataConnectors import DBConnector
from rpw.QueryTools import PepeData

"""
Initiate the real supply values for each pepe. 
"""

db_connector = DBConnector()
pepe_query_tool = PepeData(db_connector)
pepe_names = pepe_query_tool.get_pepe_names()

for pepe_name in pepe_names:
    real_supply = pepe_query_tool.derive_pepe_real_supply(pepe_name)
    query = f"UPDATE assets SET real_supply={real_supply} WHERE asset=\'{pepe_name}\'"
    print(query)
    db_connector.execute(query)
