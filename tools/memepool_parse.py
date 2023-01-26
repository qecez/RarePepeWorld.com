#!/usr/bin/env python3
import sys, os
import logging
from pprint import pprint, pformat
import pickle

# rpw package path
from time import time

sys.path.insert(0, os.environ['HOME'] + '/RarePepeWorld/')  # Run path
from rpw.QueryTools import *
from rpw.DataConnectors import *
from rpw.Utils import *
from tools.db_populate_cp import MysqlPopulator

rpc_connection = RPCConnector()
cp_data = CPData(rpc_connection)
db_connection = DBConnector()

pepe_data = PepeData(db_connection)
current_time = time()


def raw_memepool_lookup():
    method = 'get_mempool'
    params = {}
    return rpc_connection.query(
        method=method,
        params=params
    )


def dispenser_updates():
    method = 'get_mempool'
    filters = [{'field': 'category', 'op': '==', 'value': 'dispensers'},
               {'field': 'command', 'op': '==', 'value': 'update'}]
    params = {'filters': filters}
    return rpc_connection.query(
        method=method,
        params=params
    )


sample = [{'tx_hash': '19c8205b893a04d931c90335551fd8f1eb6d7eae610ee96e81d8a2e785943b37', 'command': 'insert',
            'category': 'dispenses',
            'bindings': '{"asset": "GIVEKUDOS", '
                        '"block_index": 9999999, '
                        '"destination": "1BCo7BhMvdM1RoqLmuC7WFng2VL7KT9y9Z", '
                        '"dispense_index": 0, '
                        '"dispense_quantity": 50, '
                        '"dispenser_tx_hash": "18501d8b1f51e716d7acb44b34ea7bafbf256322dcde5ec5b91845fdcb4c1aff", '
                        '"source": "178LXY38UVH6z7XLQr3i3CvuX7dp6cJPvA", '
                        '"tx_hash": "19c8205b893a04d931c90335551fd8f1eb6d7eae610ee96e81d8a2e785943b37", '
                        '"tx_index": 1757074}',
            'timestamp': 1634947373}]

mempool_raw_data = raw_memepool_lookup()['result']
mempool_dispenser_updates = dispenser_updates()['result']

print(f"Raw mempool: {pformat(mempool_raw_data)}\n")
print(f"Dispenser updates: {pformat(mempool_dispenser_updates)}\n")

print("Processing Dispenser changes...")
for mempool_item in mempool_dispenser_updates:
    print(f"Dispenser update: \n{pformat(mempool_item)}\n")




# memepool_updates = dispenser_updates()['result']

# print(f"Raw: {pformat(mempool_raw_data)}\n")
# print(f"Updates: {pformat(memepool_updates)}\n")

# for

# for update in memepool_updates:
# for update in mempool_raw_data:
#     update_binding = JSONTool.parse_json(update['bindings'])
#
# pepe_dispensers = pepe_data.get_pepe_dispensers('GIVEKUDOS')
# pprint(pepe_dispensers)
#     # matching_dispensers = [ dispenser_data for dispenser_data in pepe_dispensers if dispenser_data['source'] == update_binding['source']]
#     # print(f"Mempool: {pformat(update_binding)}\n")
#     # print(f"DB: {pformat(pepe_dispensers)}")
#     # print(f"Matching dispensers: {pformat(matching_dispensers)}")
