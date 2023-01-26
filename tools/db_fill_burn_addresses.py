#!/usr/bin/env python3
import sys, os
from pathlib import Path

os.environ['RPW_SCRIPT_BASE'] = str(Path(os.getcwd()).parent)
os.environ['RPW_LOG_PATH'] = str(Path(os.getcwd()).parent / 'logs/')
os.environ['RPW_LOG_LEVEL'] = 'DEBUG'
sys.path.insert(0, os.environ['HOME'] + '/RarePepeWorld/')  # rpw path
from rpw.DataConnectors import DBConnector

db_connection = DBConnector()

"""
Initiate burn address status for addresses in the database.
Given the list of known burn addresses, set the value of is_burn to true, for each address in the database.
"""

burn_addresses = []
burn_addresses_path = "../rpw/static/data/burn_addresses.txt"
with open(burn_addresses_path) as f:
    for raw_line in f.readlines():
        burn_addresses.append(raw_line.strip())

for burn_address in burn_addresses:
    # find matching addresses in the db
    db_query = f"SELECT * FROM addresses WHERE address='{burn_address}'"
    print(f"Query: {db_query}")
    results = db_connection.query_and_fetch(db_query)
    # insert if doesn't exist, update if does. Set as burn address.
    if len(results) == 0:
        db_query = f"INSERT INTO addresses (address,is_burn) VALUES ('{burn_address}',1)"
    else:
        db_query = f"UPDATE addresses SET is_burn={1} WHERE address='{burn_address}'"
    print(f"Query: {db_query}")
    db_connection.execute(db_query)
