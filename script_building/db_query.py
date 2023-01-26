#!/usr/bin/env python3
import sys, os
import logging
from pprint import pprint
from pathlib import Path
from random import randint, choice

os.environ['RPW_SCRIPT_BASE'] = str(Path(os.getcwd()).parent)
os.environ['RPW_LOG_PATH'] = str(Path(os.getcwd()).parent / 'logs/')
os.environ['RPW_LOG_LEVEL'] = 'DEBUG'
sys.path.insert(0, os.environ['HOME'] + '/RarePepeWorld/')  # Run path
from rpw.QueryTools import CPData, PepeData, PriceTool
from rpw.DataConnectors import RPCConnector, DBConnector
from rpw.Utils import JSONTool

db_connection = DBConnector()
pepe_data = PepeData(db_connector=db_connection)


def insert_random_ads(count: int, db_connection: None):
    def random_block_amount():
        return randint(1, 4)

    def random_pepe():
        return choice(pepe_data.get_pepe_names())

    random_ads = [(random_pepe(), '__testing__', random_block_amount()) for _ in range(count)]

    for ad in random_ads:
        query_insert = f"INSERT INTO ad_queue " \
                       f"(asset,paid_invoice,block_amount) " \
                       f"VALUES {str(tuple(ad))}"
        print(f"Query: {query_insert}")
        db_connection.execute(query_insert)


def query_test(query: str):
    return db_connection.query_and_fetch(query)


def is_burn_address(address: str) -> bool:
    query = f"SELECT is_burn FROM addresses WHERE address='{address}'"
    results = db_connection.query_and_fetch(query)
    if results:
        return bool(results[0].get('is_burn', False))
    return False


def get_btc_rate() -> float:
    query = 'SELECT usd_rate FROM prices WHERE currency=\'BTC\''
    return db_connection.query_and_fetch(query)[0].get('usd_rate', 0)


def get_pepe_names():
    """ Generates the list pepe names.  If the file storing the name, read from it. Otherwise, query
    the url containing the list of pepe names
    :return: list of strings of pepe names
    """
    query = 'SELECT asset FROM assets'
    results = db_connection.query_and_fetch(query)
    return [result['asset'] for result in results]


def get_pepe_image_file_names() -> dict:
    """ Generates the list pepe names.  If the file storing the name, read from it. Otherwise, query
    the url containing the list of pepe names
    :return: list of strings of pepe names
    """
    query = 'SELECT image_file_name FROM assets'
    results = db_connection.query_and_fetch(query)
    return {
        result['image_file_name'].split('.')[:-1][0]: result['image_file_name'] for result in results
    }


def get_featured_pepes():
    # Get current slot entries
    slots_query = "SELECT asset FROM ad_slots"
    current_slots_entries = [slot_entry['asset'] for slot_entry in db_connection.query_and_fetch(slots_query)]
    return current_slots_entries


def get_orders():
    query_get = f"SELECT * FROM orders WHERE get_asset='PEPECASH' AND status='open'"
    results = db_connection.query_and_fetch(query_get)
    return results


def get_addresses():
    query = 'SELECT DISTINCT source FROM dispensers'
    unique_addresses = set()
    db_connection.cursor.execute(query)
    addresses = db_connection.query_and_fetch(query)
    pprint(addresses)
    # for address_tup in addresses:
    #     unique_addresses.add(address_tup[0])


pprint(query_test('SELECT DISTINCT source FROM dispensers'))
print(f"{pepe_data.derive_pepe_real_supply('PEPECASH')}")