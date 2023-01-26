import os
import sys
from pathlib import Path
from pprint import pformat

os.environ['RPW_SCRIPT_BASE'] = str(Path(os.getcwd()).parent)
os.environ['RPW_LOG_PATH'] = str(Path(os.getcwd()).parent / 'logs/')
os.environ['RPW_LOG_LEVEL'] = 'DEBUG'
sys.path.insert(0, os.environ['HOME'] + '/RarePepeWorld/')  # rpw path

from rpw.DataConnectors import DBConnector, XChainConnector
from rpw.QueryTools import PepeData, XChainData
from rpw.Utils import JSONTool
from db_populate_xchain import MysqlPopulator

xchain_connector = XChainConnector()
db_connector = DBConnector()
m = MysqlPopulator()

print("Loading list of pepes...")
pepes_list = sorted(PepeData.load_pepe_names())
rarepepedirectory_urls = JSONTool.read_json_file(
    os.environ['RPW_SCRIPT_BASE'] + '/rpw/static/pepes/rarepepedirectory_links.json')
image_file_names = PepeData.load_image_file_names()
artists_file = os.environ['RPW_SCRIPT_BASE'] + '/rpw/static/pepes/pepe-artists.txt'
artists_data = JSONTool.read_json_file(artists_file)

for pepe_name in pepes_list:
    match_conditions = [{'field': 'asset', 'value': pepe_name}]
    if m.check_exists(table='assets', conditions=match_conditions):
        print(f"{pepe_name} already exists in the database. Skipping")
        continue
    else:
        asset_details_cp_raw = xchain_connector.query('asset', [pepe_name])
        print(pformat(asset_details_cp_raw))
        asset_details_cp = {
            'asset': asset_details_cp_raw['asset'],
            'asset_longname': asset_details_cp_raw['asset_longname'],
            'description': asset_details_cp_raw['description'],
            'divisible': asset_details_cp_raw['divisible'],
            'issuer': asset_details_cp_raw['issuer'],
            'locked': asset_details_cp_raw['locked'],
            'owner': asset_details_cp_raw['owner'],
            'source': artists_data[pepe_name],
            'rarepepedirectory_url': rarepepedirectory_urls.get(pepe_name,''),
            'image_file_name': image_file_names[pepe_name]
        }
        if asset_details_cp_raw['divisible']:
            asset_details_cp['supply'] = int(float(asset_details_cp_raw['supply']) * 100_000_000)
        else:
            asset_details_cp['supply'] = asset_details_cp_raw['supply']
        asset_details_cp['real_supply'] = asset_details_cp['supply']

        print(f"Asset {pepe_name} does not exist in the database. Inserting.")
        m.db_insert(table='assets', data=asset_details_cp)


