#!/usr/bin/env python3
import sys, os
from pathlib import Path

sys.path.insert(0, os.environ['HOME'] + '/RarePepeWorld/')  # Run path

import logging
logging.basicConfig(filename='../logs/result.log',
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

import qrcode
from typing import List

from rpw.QueryTools import CPData, PepeData
from rpw.DataConnectors import RPCConnector, DBConnector
from rpw.Utils import JSONTool

ADDRESS_QR_PATH= "../rpw/static/qr/"

db_connection = DBConnector(logger=logging.getLogger())
query = f"SELECT address FROM addresses"
results = db_connection.query_and_fetch(query)
for result in results:
    address = result['address']
    target = Path(ADDRESS_QR_PATH) / f'{address}.png'
    if not target.exists():
        logging.info(f"Creating {target}")
        img = qrcode.make(address)
        img.save(target)
