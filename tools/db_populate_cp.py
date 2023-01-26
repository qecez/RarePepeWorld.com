#!../venv/bin/python3
import logging
import os
from pprint import pprint

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

logging.basicConfig(filename='../logs/db_populate.log',
                    level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

STATE_FILE = "../rpw/static/data/db_latest_block"
ADDRESS_LIST = "../rpw/static/data/addresses.txt"
ADDRESS_QR_PATH = "../rpw/static/qr/"


class MysqlPopulator:

    def __init__(self, pepe_populator_mode=True, source="cp_node"):
        # Connections
        self.db_connection = DBConnector()
        if pepe_populator_mode:
            # Data Sources
            self.pepe_query_tool = PepeData(self.db_connection)
            if source == "xchain":
                self.data_connection = XChainConnector()
                self.cp_data = XChainData(self.data_connection)
            else:
                self.data_connection = RPCConnector()
                self.cp_data = CPData(self.data_connection)
            self.pepes_list = self.pepe_query_tool.get_pepe_names()
            self.last_db_block = self.get_latest_db_block()
            self.current_block = self.cp_data.get_cp_last_block()

    def check_exists(self, table: str = "", conditions=None):
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
        logging.debug(f"MySQL execute: {query}")
        self.db_connection.cursor.execute(query)
        insert_id = self.db_connection.cursor.lastrowid
        logging.debug(f"Successful inserted data with id# {insert_id},")

    def db_update(self, table: str = "", data=None, match_conditions=None):
        if data is None:
            data = {}
        if match_conditions is None:
            match_conditions = []
        data = self.prep_dict_for_db(data)
        logging.debug(f"match_conditions: {match_conditions}")
        conditions_str = self.create_conditions_string(match_conditions)
        updates = [f"{key}={value}" for key, value in data.items()]
        updates_str = ', '.join(updates)
        logging.debug(updates)
        logging.debug(updates_str)
        query = f"UPDATE {table} SET {updates_str} WHERE {conditions_str}"
        logging.debug(query)
        logging.debug(f"MySQL execute: {query}")
        self.db_connection.cursor.execute(query)
        self.db_connection.commit()

    def process_asset(self, pepe_data: dict) -> bool:
        logging.debug(f"Processing asset: {pepe_data}")
        match_conditions = [{'field': 'asset', 'value': pepe_data['asset']}]
        pepe_data['description'] = pepe_data['description'][:250]  # truncate description to 250 characters
        pepe_data['real_supply'] = self.pepe_query_tool.derive_pepe_real_supply(pepe_data['asset'])
        if self.check_exists(table='assets', conditions=match_conditions):
            logging.debug(f"Asset {pepe_data['asset']} already exists in the database. Updating.")
            match_conditions = [{'field': 'asset', 'value': pepe_data['asset']}]
            self.db_update(table="assets", data=pepe_data, match_conditions=match_conditions)
        else:
            logging.debug(f"Asset {pepe_data['asset']} does not exist in the database. Inserting.")
            self.db_insert(table='assets', data=pepe_data)
        return True

    def process_holding(self, holder_data: dict, asset: str):
        logging.debug(f"\nHolder Record: {holder_data}")
        match_conditions = [{'field': 'asset', 'value': asset},
                            {'field': 'address', 'value': holder_data['address']}]
        if self.check_exists(table='holdings', conditions=match_conditions):
            logging.debug(
                f"Holder of asset {asset} of address {holder_data['address']} "
                f"already exists in the database. Updating.")
            self.db_update(table='holdings', data=holder_data, match_conditions=match_conditions)
        else:
            holder_data['asset'] = asset
            logging.debug(
                f"Holder of asset {asset} of address {holder_data['address']} "
                f"does not exist in the database. Inserting.")
            self.db_insert(table='holdings', data=holder_data)

    def process_addresses(self):
        logging.info("Adding addresses to the database.")
        unique_addresses = set()
        query = 'SELECT DISTINCT source FROM dispensers'
        results = self.db_connection.query_and_fetch(query)
        for result in results:
            unique_addresses.add(result['source'])
        for address in unique_addresses:
            conditions = [{'field': 'address', 'value': address}]
            if not self.check_exists('addresses', conditions):
                logging.info(f"Adding {address} to the database.")
                query = f"INSERT INTO addresses (address) VALUES (\'{address}\') " \
                        f"ON DUPLICATE KEY UPDATE address=\'{address}\'"
                self.db_connection.execute(query)
        logging.info("Done.")

    def generate_qr_codes(self):
        query = f"SELECT address FROM addresses"
        results = self.db_connection.query_and_fetch(query)
        for result in results:
            address = result['address']
            target = Path(ADDRESS_QR_PATH) / f'{address}.png'
            if not target.exists():
                logging.info(f"Creating {target}")
                img = qrcode.make(address)
                img.save(target)

    def process_dispenser(self, dispenser_data: dict):
        logging.debug(f"\nDispenser Record: {dispenser_data}")
        conditions = [{'field': 'tx_index', 'value': dispenser_data['tx_index']}]
        if self.check_exists(table='dispensers', conditions=conditions):
            logging.debug(f"Dispenser with tx_index: {dispenser_data['tx_index']} "
                          f"already exists in the database. Updating.")
            self.db_update(table='dispensers', data=dispenser_data, match_conditions=conditions)
        else:
            logging.debug((f"Dispenser with tx_index: {dispenser_data['tx_index']} "
                           f"does not exist in the database. Inserting."))
            self.db_insert(table='dispensers', data=dispenser_data)

    def process_order(self, order_data: dict, pepe_name: str = ''):
        if not pepe_name:
            pepe_name = order_data['get_asset']
        logging.debug(f"\nOrder Record: {order_data}")
        match_conditions = [{'field': 'tx_index', 'value': order_data['tx_index']}]
        if self.check_exists(table='orders', conditions=match_conditions):
            logging.debug(
                f"{pepe_name} order with transaction index {order_data['tx_index']} "
                f"already exists in the database. Updating.")
            self.db_update(table='orders', data=order_data, match_conditions=match_conditions)
        else:
            logging.debug(
                f"{pepe_name} order with transaction index {order_data['tx_index']} "
                f"does not exist in the database. Inserting.")
            self.db_insert(table='orders', data=order_data)

    def initiate_db_lastest_block_sync(self):
        logging.info(f"Updating db")
        # assets referenced in block
        if self.current_block == self.last_db_block:
            logging.info("DB is already synced up. Skipping")
            exit()
        # list pepes updated from current block to last block
        pepes_sublist = self.get_pepes_in_block(range(self.last_db_block, self.current_block))
        self.sync_pepe_list(sorted(pepes_sublist))

    def initiate_db_full_sync(self):
        logging.info("Populating list of pepe assets...")
        self.sync_pepe_list(self.pepes_list)

    def sync_pepe_list(self, pepes_sublist):
        logging.info(f"Updating db")
        # populate data for the provided list of pepe names
        logging.info(f"Updating records for pepes:\n {pepes_sublist}")
        for pepe_name in pepes_sublist:
            logging.info(f"Pepe: {pepe_name}")
            asset_details_cp = self.cp_data.get_pepes_details(pepe_name)
            logging.debug(pretty_print_dict("Cp details", asset_details_cp))
            asset_details_db = self.pepe_query_tool.get_pepe_details(pepe_name)
            logging.debug(pretty_print_dict("Db details", asset_details_db))
            self.process_asset(asset_details_cp)

            logging.debug("Populating pepe holders into the detabase...")
            holders_list = [holder_data for holder_data in self.cp_data.get_pepe_holdings(pepe_name)]
            logging.debug(pprint(f"Holder details: {holders_list}"))
            # calculate each addresses quantities
            address_list = set([holding['address'] for holding in holders_list])
            for address in address_list:
                address_holdings = sum(
                    [int(holding['address_quantity']) for holding in holders_list if holding['address'] == address])
                address_data = {
                    'address': address,
                    'address_quantity': address_holdings,
                    'escrow': None
                }
                self.process_holding(holder_data=address_data, asset=pepe_name)

            logging.debug("Populating pepe dispensers into the detabase")
            dispensers_list = self.cp_data.get_pepe_dispensers(pepe_name)
            logging.debug(pretty_print_dict("Dispensers details", dispensers_list))
            for dispenser_data in dispensers_list:
                self.process_dispenser(dispenser_data=dispenser_data)

            logging.debug("Populating pepe orders into the datablase")
            if pepe_name in ['XCP', 'PEPECASH']:
                base_asset = 'XCP' if pepe_name == 'PEPECASH' else 'XCP'
            else:
                base_asset = ''
            current_db_orders_dict = self.pepe_query_tool.get_pepe_orders(pepe_name, base_asset=base_asset)
            current_cp_orders_dict = self.cp_data.get_pepe_orders(pepe_name)
            current_db_orders_tx_hashes = [current_order['tx_hash'] for current_order in
                                     current_db_orders_dict['get'] + current_db_orders_dict['give']]
            current_cp_orders_tx_hashes = [current_order['tx_hash'] for current_order in
                                     current_cp_orders_dict['get'] + current_cp_orders_dict['give']]
            new_cp_orders = set(current_cp_orders_tx_hashes) - set(current_db_orders_tx_hashes)
            for order_tx_hash in current_db_orders_tx_hashes:
                for order in current_db_orders_dict:
                    if order['tx_hash'] == order_tx_hash:
                        # details = self.cp_data.get_order_by_hash(order_tx_hash)
                        details = order
                if details:
                    # print(f"Update: {details}")
                    self.process_order(details, pepe_name)
            for order_tx_hash in new_cp_orders:
                for order in current_cp_orders_dict:
                    if order['tx_hash'] == order_tx_hash:
                        details = order
                        # details = self.cp_data.get_order_by_hash(order_tx_hash)
                if details:
                    # print(f"Insert: {details}")
                    self.process_order(details, pepe_name)

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

    # db_connector = MySQLConnector()
    m = MysqlPopulator()
    if len(sys.argv) > 1:
        if sys.argv[1] == 'full':  # update entire pepe database
            # first pass: update all pepes up to the block current at time of script launch
            m.initiate_db_full_sync()
            # second pass: update blocks that occurred during the first pass
            last_block = m.current_block
            m.current_block = m.cp_data.get_cp_last_block()
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
        elif sys.argv[1] == 'addresses':  # only do addresses
            m.process_addresses()
            # m.generate_qr_codes()
            exit()
    else:
        display_syntax()
        exit()
    m.process_addresses()
    m.generate_qr_codes()
