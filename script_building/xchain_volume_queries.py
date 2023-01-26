# -*- coding: utf-8 -*-
from pathlib import Path
from pprint import pformat
import requests
import json

base_url = "https://www.xchain.io/api"
order_matches_url = f"{base_url}/order_matches/_block_"
issuances_url = f"{base_url}/issuances/_block_"
markets_url = f"{base_url}/markets"


def get_volume():
    # initial_block = 278_270
    # latest_block = 731_737
    # for i in range(latest_block,latest_block-5,-1):
    #     print (i)
    if Path('volume_data.json').exists():
        with open('volume_data.json') as f:
            json_str = [s.strip() for s in f.readlines()]
            return json.loads(''.join(json_str))
    else:
        data_raw = requests.get(markets_url).content
        data_json = json.loads(data_raw)
        with open('volume_data.json', 'w') as f:
            f.writelines(json.dumps(data_json))
        return data_json


def get_assets(data_set):
    pass


# print(pformat(block_data_json))
block_data_json = get_volume()

count = 0
for datum in block_data_json['data']:
    # print(pformat(datum))
    asset_give, asset_get = str(datum['name']).split('/')
    volume_give, volume_get = str(datum['24hour']['volume']).split('|')
    if float(volume_give) > 0 or float(volume_get) > 0:
        print(f'Give asset: {asset_give}, Give volume: {volume_give}\n'
              f'Get asset: {asset_get}, Get volume: {volume_get}\n')
        count += 1
print(count)
