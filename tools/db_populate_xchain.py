#!../venv/bin/python3
import logging
import os
from pprint import pprint, pformat

import qrcode
import sys
from pathlib import Path

os.environ['RPW_SCRIPT_BASE'] = str(Path(os.getcwd()).parent)
os.environ['RPW_LOG_PATH'] = str(Path(os.getcwd()).parent / 'logs/')
os.environ['RPW_LOG_LEVEL'] = 'DEBUG'
sys.path.insert(0, os.environ['HOME'] + '/RarePepeWorld/')  # Run path for rpw modules
from rpw.DataConnectors import RPCConnector, DBConnector, XChainConnector
from rpw.QueryTools import CPData, PepeData, XChainData
from rpw.Utils import JSONTool

STATE_FILE = "../rpw/static/data/db_latest_block"
ADDRESS_LIST = "../rpw/static/data/addresses.txt"
RAREPEPE_DIRECTORY_URLS = "../rpw/static/pepes/rarepepedirectory_links.json"
ADDRESS_QR_PATH = "../rpw/static/qr/"


class MysqlPopulator:
    """ Class for performing updates to the Mysql database for site data. """

    def __init__(self, pepe_populator_mode=True):
        """
        Initialize populator
        :param pepe_populator_mode: if False, object can be used without triggering various data lookups
        """
        self.db_connection = DBConnector()
        if pepe_populator_mode:
            # Data Sources
            self. \
                pepe_query_tool = PepeData(self.db_connection)
            self.data_connection = XChainConnector()
            self.cp_data = XChainData(self.data_connection)
            self.pepes_list = self.pepe_query_tool.get_pepe_names()
            self.last_db_block = self.get_latest_db_block()
            self.current_block = self.cp_data.get_btc_current_block()

    def check_exists(self, table: str = "", conditions=None):
        """
        Ensure the table with the desired conditions are valid.
        :param table: table to check
        :param conditions: set of conditions to test for
        :return: True if met, False otherwise
        """
        if conditions is None:
            conditions = {}
        columns = []
        for condition in conditions:
            column = condition['field']
            columns.append(column)
        conditions_string = self.create_conditions_string(conditions)
        columns_string = ','.join(columns)

        check_query = f"SELECT {columns_string} FROM {table} WHERE {conditions_string} LIMIT 1"
        self.db_connection.cursor.execute(check_query)
        result = self.db_connection.cursor.fetchall()
        if not result:
            return False
        else:
            return True

    def create_conditions_string(self, conditions: dict):
        conditions_strings = []
        for condition in conditions:
            column = condition['field']
            value = self.prep_object_for_mysql(condition['value'])
            conditions_strings.append(f"{column}={value}")
        conditions_string = ' AND '.join(conditions_strings)
        return conditions_string

    def prep_object_for_mysql(self, value: object):
        obj_type = type(value)
        if obj_type in [int, float, complex, None]:
            new = str(value)
        elif obj_type == bool:
            new = '1' if value else '0'
        elif value is None:
            new = '\"\"'
        else:  # 'str' and all other types
            new = f"\'{self.db_connection.converter.escape(value)}\'"
        return new

    def prep_dict_for_db(self, data: dict):
        if type(data) == dict:
            new = {}
            for key, value in data.items():
                new[key] = self.prep_object_for_mysql(value)
            return new

    @staticmethod
    def get_latest_db_block():
        with open(STATE_FILE) as f:
            result = f.readline().strip()
        return int(result)

    @staticmethod
    def write_latest_db_block(block_number: int):
        with open(STATE_FILE, 'w') as f:
            f.write(str(block_number) + '\n')

    def db_insert(self, table: str, data: dict, append: str = ""):
        data = self.prep_dict_for_db(data)
        columns_str = ', '.join([column for column in data.keys()])
        values_str = ", ".join([str(value) for value in data.values()])
        query = f"INSERT INTO {table} ({columns_str}) values ({values_str})"
        if append:
            query += f" {append}"
        print(f"MySQL execute: {query}")
        self.db_connection.cursor.execute(query)
        insert_id = self.db_connection.cursor.lastrowid
        print(f"Successful inserted data with id# {insert_id},")

    def db_update(self, table: str = "", data=None, match_conditions=None):
        if data is None:
            data = {}
        if match_conditions is None:
            match_conditions = []
        print(f"Db Update: {pformat(data)}")
        print(f"Match_conditions: {match_conditions}")
        data = self.prep_dict_for_db(data)
        conditions_str = self.create_conditions_string(match_conditions)
        updates = [f"{key}={value}" for key, value in data.items()]
        updates_str = ', '.join(updates)
        print(f"Updates: {updates_str}")
        query = f"UPDATE {table} SET {updates_str} WHERE {conditions_str}"
        print(f"MySQL execute: {query}")
        self.db_connection.cursor.execute(query)
        self.db_connection.commit()

    def process_asset(self, pepe_data: dict) -> bool:
        print(f"Processing asset: {pepe_data}")
        match_conditions = [{'field': 'asset', 'value': pepe_data['asset']}]
        pepe_data['description'] = pepe_data['description'][:250]  # truncate description to 250 characters
        pepe_data['real_supply'] = self.pepe_query_tool.derive_pepe_real_supply(pepe_data['asset'])
        if self.check_exists(table='assets', conditions=match_conditions):
            print(f"Asset {pepe_data['asset']} already exists in the database. Updating.")
            match_conditions = [{'field': 'asset', 'value': pepe_data['asset']}]
            self.db_update(table="assets", data=pepe_data, match_conditions=match_conditions)
        else:
            print(f"Asset {pepe_data['asset']} does not exist in the database. Inserting.")
            self.db_insert(table='assets', data=pepe_data)
        return True

    def process_holding(self, holder_data: dict, asset: str):
        print(f"\nHolder Record: {pformat(holder_data)}")
        match_conditions = [{'field': 'asset', 'value': asset},
                            {'field': 'address', 'value': holder_data['address']}]
        if self.check_exists(table='holdings', conditions=match_conditions):
            print(
                f"Holder of asset {asset} of address {holder_data['address']} "
                f"already exists in the database. Updating.")
            self.db_update(table='holdings', data=holder_data, match_conditions=match_conditions)
        else:
            holder_data['asset'] = asset
            print(
                f"Holder of asset {asset} of address {holder_data['address']} "
                f"does not exist in the database. Inserting.")
            self.db_insert(table='holdings', data=holder_data)

    def process_addresses(self):
        print("Adding addresses to the database.")
        unique_addresses = set()
        query = 'SELECT DISTINCT source FROM dispensers'
        results = self.db_connection.query_and_fetch(query)
        for result in results:
            unique_addresses.add(result['source'])
        for address in unique_addresses:
            conditions = [{'field': 'address', 'value': address}]
            if not self.check_exists('addresses', conditions):
                print(f"Adding {address} to the database.")
                query = f"INSERT INTO addresses (address) VALUES (\'{address}\') " \
                        f"ON DUPLICATE KEY UPDATE address=\'{address}\'"
                self.db_connection.execute(query)
        print("Done.")

    def generate_qr_codes(self):
        query = f"SELECT address FROM addresses"
        results = self.db_connection.query_and_fetch(query)
        for result in results:
            address = result['address']
            target = Path(ADDRESS_QR_PATH) / f'{address}.png'
            if not target.exists():
                print(f"Creating {target}")
                img = qrcode.make(address)
                img.save(target)

    def process_dispenser(self, dispenser_data: dict):
        print(f"\nDispenser Record: {pformat(dispenser_data)}")
        conditions = [{'field': 'tx_index', 'value': dispenser_data['tx_index']}]
        if self.check_exists(table='dispensers', conditions=conditions):
            print(f"Dispenser with tx_index: {dispenser_data['tx_index']} "
                  f"already exists in the database. Updating.")
            self.db_update(table='dispensers', data=dispenser_data, match_conditions=conditions)
        else:
            print((f"Dispenser with tx_index: {dispenser_data['tx_index']} "
                   f"does not exist in the database. Inserting."))
            self.db_insert(table='dispensers', data=dispenser_data)

    def process_order(self, order_data: dict, pepe_name: str = ''):
        if not pepe_name:
            pepe_name = order_data['get_asset']
        print(f"\nOrder Record: {pformat(order_data)}")

        match_conditions = [{'field': 'tx_index', 'value': order_data['tx_index']}]
        if self.check_exists(table='orders', conditions=match_conditions):
            print(
                f"{pepe_name} order with transaction index {order_data['tx_index']} "
                f"already exists in the database. Updating.")
            self.db_update(table='orders', data=order_data, match_conditions=match_conditions)
        else:
            print(
                f"{pepe_name} order with transaction index {order_data['tx_index']} "
                f"does not exist in the database. Inserting.")
            self.db_insert(table='orders', data=order_data)

    def initiate_db_lastest_block_sync(self):
        print(f"Updating db")
        # assets referenced in block
        if self.current_block == self.last_db_block:
            print("DB is already synced up. Skipping")
            exit()
        # list pepes updated from current block to last block
        pepes_sublist = self.get_pepes_in_block(range(self.last_db_block, self.current_block))
        self.sync_pepe_list(sorted(pepes_sublist))

    def initiate_asset_db(self, pepes_to_initiate):
        rarepepedirectory_urls = JSONTool.read_json_file(RAREPEPE_DIRECTORY_URLS)
        image_file_names = PepeData.load_image_file_names()

        for pepe_name in pepes_to_initiate:
            asset_details_cp = self.cp_data.get_pepe_details(pepe_name)
            print(f"CP Asset details: {pformat(asset_details_cp)}")
            asset_details_cp['rarepepedirectory_url'] = rarepepedirectory_urls[pepe_name]
            asset_details_cp['image_file_name'] = image_file_names[pepe_name]
            asset_details_cp['real_supply'] = asset_details_cp['supply']
            print(f"Cp Asset details, parsed: {asset_details_cp}")
            self.process_asset(asset_details_cp)

    def initiate_db_full_sync(self):
        print("Populating list of pepe assets...")
        self.sync_pepe_list(self.pepes_list)

    def sync_pepe_list(self, pepes_sublist):
        print(f"Updating db")
        # populate data for the provided list of pepe names
        print(f"Updating records for pepes:\n {pepes_sublist}")
        for pepe_name in pepes_sublist:
            print(f"Pepe: {pepe_name}")
            asset_details_cp = self.cp_data.get_pepe_details(pepe_name)
            print(f"Cp details: {pformat(asset_details_cp)}")
            asset_details_db = self.pepe_query_tool.get_pepe_details(pepe_name)
            print(f"Db details: {pformat(asset_details_db)}")
            self.process_asset(asset_details_cp)

            print("Populating pepe holders into the database...")
            # holders_list = [holder_data for holder_data in self.cp_data.get_pepe_holdings(pepe_name)]
            holders_list = self.cp_data.get_pepe_holdings(pepe_name)
            print(f"CP Holder details: {pformat(holders_list)}")

            # calculate each addresses quantities
            address_list = set([holding['address'] for holding in holders_list])
            for address in address_list:
                address_holdings = sum(
                    [int(float(holding['address_quantity'])) for holding in holders_list if
                     holding['address'] == address])
                address_data = {
                    'address': address,
                    'address_quantity': address_holdings,
                    'escrow': None
                }
                self.process_holding(holder_data=address_data, asset=pepe_name)

            print("Populating pepe dispensers into the database")
            dispensers_list = self.cp_data.get_pepe_dispensers(pepe_name)
            print(f"Dispensers details {pformat(dispensers_list)}")
            for dispenser_data in dispensers_list:
                self.process_dispenser(dispenser_data=dispenser_data)

            print("Populating pepe orders into the database")
            if pepe_name in ['XCP', 'PEPECASH']:
                base_asset = 'XCP' if pepe_name == 'PEPECASH' else 'XCP'
            else:
                base_asset = ''
            current_db_orders_dict = self.pepe_query_tool.get_pepe_orders(pepe_name, base_asset=base_asset)
            current_cp_orders_dict = self.cp_data.get_pepe_orders(pepe_name)
            current_cp_orders_by_hash = {od['tx_hash']: od
                                         for od in current_cp_orders_dict['give'] + current_cp_orders_dict['get']}
            print(f"DB Orders: {pformat(current_db_orders_dict)}")
            print(f"CP Orders: {pformat(current_cp_orders_dict)}")
            current_db_orders_tx_hashes = [current_order['tx_hash'] for current_order in
                                           current_db_orders_dict.get('get', [])
                                           + current_db_orders_dict.get('give', [])]
            current_cp_orders_tx_hashes = [current_order['tx_hash'] for current_order in
                                           current_cp_orders_dict.get('get', [])
                                           + current_cp_orders_dict.get('give', [])]
            new_cp_orders = set(current_cp_orders_tx_hashes) - set(current_db_orders_tx_hashes)
            for order_tx_hash in current_db_orders_tx_hashes:
                order_details = {}
                for order in current_db_orders_dict['give'] + current_db_orders_dict['get']:
                    if order['tx_hash'] == order_tx_hash:
                        order_details = current_cp_orders_by_hash[order_tx_hash]
                if order_details:
                    self.process_order(order_details, pepe_name)
            for order_tx_hash in new_cp_orders:
                order_details = {}
                for order in current_cp_orders_dict['give'] + current_cp_orders_dict['get']:
                    if order['tx_hash'] == order_tx_hash:
                        order_details = current_cp_orders_by_hash[order_tx_hash]
                if order_details:
                    self.process_order(order_details, pepe_name)

    def get_pepes_in_block(self, block_numbers: list or str):
        if type(block_numbers) == str:
            block_numbers = [block_numbers]
        pepes_set = set()
        for block_number in block_numbers:
            pepes_set.update(self.cp_data.pepe_pepes_in_block(block_number, self.pepes_list))
        return pepes_set


def pretty_print_dict(message: str, data: dict):
    print(f"{message}: {JSONTool.parse_dict(data, **JSONTool.JSON_PRETTY_KWARGS)}")


def display_syntax():
    print("db_populate.sh [full]|[list pepe_name,pepe_name,...]|[sync]|[addresses]")


if __name__ == "__main__":

    m = MysqlPopulator()
    if len(sys.argv) > 1:
        if sys.argv[1] == 'full':  # update entire pepe database
            # first pass: update all pepes up to the block current at time of script launch
            m.initiate_db_full_sync()
            # second pass: update blocks that occurred during the first pass
            last_block = m.current_block
            m.current_block = m.cp_data.get_btc_current_block()
            pepes_list = m.get_pepes_in_block(range(last_block, m.current_block + 1))
            m.sync_pepe_list(pepes_list)
            m.write_latest_db_block(m.current_block)
        elif sys.argv[1] == 'list':  # process a given comma separated list of pepes
            if len(sys.argv) != 3:
                display_syntax()
                exit(1)
            else:
                pepes_list = sys.argv[2].split(',')
                m.sync_pepe_list(pepes_list)
        elif sys.argv[1] == 'sync':  # process latest blocks
            m.initiate_db_lastest_block_sync()
            m.write_latest_db_block(m.current_block)
        elif sys.argv[1] == 'initiate':
            if len(sys.argv) > 2:
                pepes_list = sys.argv[2].split(',')
            else:
                pepes_list = m.pepes_list
            m.initiate_asset_db(pepes_list)
            exit()
        elif sys.argv[1] == 'addresses':  # only do addresses
            m.process_addresses()
            m.generate_qr_codes()
            exit()
    else:
        display_syntax()
        exit()
    m.process_addresses()
    m.generate_qr_codes()
