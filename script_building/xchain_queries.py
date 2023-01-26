# -*- coding: utf-8 -*-
import logging
import sys, os
from pathlib import Path
from pprint import pprint,pformat

os.environ['RPW_SCRIPT_BASE'] = str(Path(os.getcwd()).parent)
os.environ['RPW_LOG_PATH'] = str(Path(os.getcwd()).parent / 'logs/')
os.environ['RPW_LOG_LEVEL'] = 'DEBUG'

sys.path.insert(0, os.environ['HOME'] + '/RarePepeWorld/')  # Run path
logging.basicConfig(filename='../logs/result.log',
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')  # Debugging

from rpw.DataConnectors import XChainConnector, DBConnector
from rpw.QueryTools import PepeData

xchain_connection = XChainConnector()

db_connector = DBConnector()
pepe_query_tool = PepeData(db_connector)
pepes_list = pepe_query_tool.get_pepe_names()

pepe_name = 'XCP'
# pepe_name = 'PEPETHUGLIFE'
print(f"Test asset: {pepe_name}")

pepe_dispensers = xchain_connection.query('dispensers',['BERNIEPEPE'])

print(pformat(pepe_dispensers))