#!/usr/bin/env python3
import sys, os
import logging
from pprint import pprint, pformat
from pathlib import Path

os.environ['RPW_SCRIPT_BASE'] = str(Path(os.getcwd()).parent)
os.environ['RPW_LOG_PATH'] = str(Path(os.getcwd()).parent / 'logs/')
os.environ['RPW_LOG_LEVEL'] = 'DEBUG'
sys.path.insert(0, os.environ['HOME'] + '/RarePepeWorld/')  # Run path

from rpw.QueryTools import DBConnector, PepeData
from rpw.PagesData import PepePage, CommonPageData, PriceTool, Formats, PepeHolders
from rpw.Logging import Logger

loggers = {
    'root': Logger.setup_logger('root', logging.getLogger('root')),
    'data': Logger.setup_logger('data', logging.getLogger('data')),
    'data_queries': Logger.setup_logger('data_queries', logging.getLogger('data_queries')),
    'errors': Logger.setup_logger('errors', logging.getLogger('errors')),
    'purchases': Logger.setup_logger('purchases', logging.getLogger('purchases'))
}


class PepePage:
    def __init__(self):
        pass

    @staticmethod
    def create(pepe_name, dispenser_number: int = 0, loggers=None, fiat_enabled=False):
        if loggers is None:
            loggers = {'data': logging.getLogger('data')}
        db_connection = DBConnector(loggers=loggers)
        pepe_query_tool = PepeData(db_connection, loggers=loggers)
        general_page_data = CommonPageData.create()
        price_tool = PriceTool(db_connection, loggers=loggers)

        pepe_details = pepe_query_tool.get_pepe_details(pepe_name)

        pepe_dispensers_data = PepeDispensers.create(pepe_name,
                                                     pepe_query_tool=pepe_query_tool,
                                                     price_tool=price_tool,
                                                     pepe_details=pepe_details,
                                                     fiat_enabled=fiat_enabled,
                                                     loggers=loggers)
        pepe_xcp_orders_data = PepeOrders.create(pepe_name,
                                                 base_asset='XCP',
                                                 pepe_query_tool=pepe_query_tool,
                                                 price_tool=price_tool,
                                                 pepe_details=pepe_details,
                                                 fiat_enabled=fiat_enabled,
                                                 loggers=loggers)
        pepe_pepecash_orders_data = PepeOrders.create(pepe_name,
                                                      base_asset='PEPECASH',
                                                      pepe_query_tool=pepe_query_tool,
                                                      price_tool=price_tool,
                                                      pepe_details=pepe_details,
                                                      fiat_enabled=fiat_enabled,
                                                      loggers=loggers)
        pepe_holders_data = PepeHolders.create(pepe_name,
                                               pepe_query_tool=pepe_query_tool,
                                               pepe_details=pepe_details,
                                               show_holder_count=10,
                                               pepe_dispensers=pepe_dispensers_data,
                                               loggers=loggers)

        if len(pepe_dispensers_data['rows']) == 0:
            shown_dispenser_price = ''
            shown_dispenser_address = ''
            shown_dispenser_address_truncated = ''
            shown_dispenser_qrcode = ''
            shown_dispenser_price_btc = ''
            shown_dispenser_usd_value = ''
            shown_dispenser_stock = ''
            shown_dispenser_receive = ''
            shown_dispenser_xchain_url = ''
        else:
            shown_dispenser_price = pepe_dispensers_data['rows'][dispenser_number]['pay']
            shown_dispenser_price_btc = pepe_dispensers_data['rows'][dispenser_number]['pay_btc']
            shown_dispenser_address = pepe_dispensers_data['rows'][dispenser_number]['address']
            shown_dispenser_address_truncated = f"{shown_dispenser_address[:5] + '...' + shown_dispenser_address[-5:]}"
            shown_dispenser_qrcode = f"qr/{shown_dispenser_address}.png"
            shown_dispenser_usd_value = pepe_dispensers_data['rows'][dispenser_number]['usd_value']
            shown_dispenser_stock = pepe_dispensers_data['rows'][dispenser_number]['stock']
            shown_dispenser_receive = pepe_dispensers_data['rows'][dispenser_number]['receive']
            shown_dispenser_xchain_url = pepe_dispensers_data['rows'][dispenser_number]['xchain_tx_url']

        pepe_page_data = {
            **general_page_data,
            'pepe_details': pepe_details,
            'pepe_dispensers': pepe_dispensers_data,
            'pepe_xcp_orders': pepe_xcp_orders_data,
            'pepe_pepecash_orders': pepe_pepecash_orders_data,
            'pepe_holders': pepe_holders_data,
            'pepe_name': pepe_name,
            'supply': Formats.pepe_normalized_supply_str(pepe_details['supply'], pepe_details['divisible']),
            'series': pepe_details['series'],
            'pepe_rarepepedirectory_url': pepe_details['rarepepedirectory_url'],
            'pepe_xchain_url': f"https://xchain.io/asset/{pepe_name}",
            'pepe_artist': pepe_details['source'],
            'pepe_image_url': pepe_dispensers_data['pepe_image_url'],
            'latest_price': "Under development",
            'pepe_images': pepe_query_tool._pepe_images,
            'dispenser_number': dispenser_number,
            'dispenser_count': len(pepe_dispensers_data['rows']),
            'shown_dispenser_price': shown_dispenser_price,
            'shown_dispenser_price_btc': shown_dispenser_price_btc,
            'shown_dispenser_address': shown_dispenser_address,
            'shown_dispenser_address_truncated': shown_dispenser_address_truncated,
            'shown_dispenser_qrcode': shown_dispenser_qrcode,
            'shown_dispenser_usd_value': shown_dispenser_usd_value,
            'shown_dispenser_receive': shown_dispenser_receive,
            'shown_dispenser_stock': shown_dispenser_stock,
            'shown_dispenser_xchain_url': shown_dispenser_xchain_url,
            'show_xcp_orders': pepe_name != 'XCP',
            'show_pepecash_orders': pepe_name != 'PEPECASH',
            'fiat_enabled': fiat_enabled
        }
        db_connection.close()

        loggers['data'].info(f"Pepe page data: {pformat(pepe_page_data)}")
        return pepe_page_data


class PepeOrders:
    def __init__(self):
        pass

    @staticmethod
    def create(
            pepe_name: str,
            base_asset: str = "XCP",
            pepe_query_tool: PepeData = None,
            price_tool: PriceTool = None,
            pepe_details=None,
            fiat_enabled=False,
            loggers=None
    ):
        if loggers is None:
            loggers = {'data': logging.getLogger('data')}
        pepe_sell_orders_data = sorted(
            pepe_query_tool.get_pepe_orders(pepe_name, status='open', base_asset=base_asset)['give'],
            key=lambda x: x['give_quantity'] / x['get_quantity'], reverse=True
        )
        pepe_buy_orders_data = sorted(
            pepe_query_tool.get_pepe_orders(pepe_name, status='open', base_asset=base_asset)['get'],
            key=lambda x: x['get_quantity'] / x['give_quantity']
        )
        output_order_type = {
            'get': 'buy',
            'give': 'sell'
        }
        pepe_image_url = 'pepes/images/' + pepe_query_tool._pepe_images[pepe_name]
        pepe_thumbnail_url = 'pepes/images_thumbnails/' + pepe_query_tool._pepe_images[pepe_name]
        base_asset_image_url = 'pepes/images_thumbnails/' + pepe_query_tool._pepe_images[base_asset]
        table_headers = ['BTC', 'Price', 'Stock'] if not fiat_enabled else ['USD', 'BTC', 'Price', 'Stock']
        data_output = {
            'table_title': f'{base_asset} DEX',
            'buy_header': 'Buy Orders',
            'sell_header': 'Sell Orders',
            'table_headers': table_headers,
            'base_asset_header': 'Price',
            'pepe_asset_header': 'Stock',
            'pepe_url': f"/{pepe_name}",
            'pepe_image_url': pepe_image_url,
            'pepe_thumbnail_url': pepe_thumbnail_url,
            'base_asset_url': f"/{base_asset}",
            'base_asset_image_url': base_asset_image_url,
            'btc_image_url': 'images/btc.jpg',
            'buy_orders': [],
            'sell_orders': [],
            'fiat_enabled': fiat_enabled,
            'buy': {
                'header': 'Buy Orders',
                'orders': []
            },
            'sell': {
                'header': 'Sell Orders',
                'orders': []
            }
        }
        for db_order_type in ['get', 'give']:
            if db_order_type == 'get':
                order_data_set = pepe_buy_orders_data
                base_asset_type = 'give'
            else:
                order_data_set = pepe_sell_orders_data
                base_asset_type = 'get'
            for i, order_data in enumerate(order_data_set):
                pepe_units = Formats.pepe_units_normalize(
                    order_data[f'{db_order_type}_quantity'],
                    divisible=pepe_details['divisible'])
                base_units = Formats.pepe_units_normalize(
                    order_data[f'{base_asset_type}_quantity'],
                    divisible=True)
                pepe_stock = Formats.pepe_quantity_str(
                    order_data[f'{db_order_type}_remaining'], divisible=pepe_details['divisible'])
                pepe_price_int = base_units / pepe_units
                pepe_price_str = Formats.format_base_asset(pepe_price_int)
                convert_rate = price_tool.get_xcp_rate() if base_asset == 'XCP' else price_tool.get_pepecash_rate()
                price_in_btc = Formats.satoshis_to_str(
                    convert_rate * pepe_price_int / price_tool.get_btc_rate() * 10 ** 8)
                usd_value = f"${pepe_price_int * convert_rate:,.2f}"
                order_values = {
                    'pepe_amount': pepe_stock,
                    'pepe_price': pepe_price_str,
                    'pepe_price_btc': price_in_btc,
                    'usd_value': usd_value,
                    'xchain_tx_url': f"https://xchain.io/tx/{order_data['tx_index']}"
                }
                data_output[output_order_type[db_order_type]]['orders'].append(order_values)

        loggers['data'].info(f"Search results data: {pformat(data_output)}")
        return data_output


class PepeDispensers:
    def __init__(self):
        pass

    @staticmethod
    def create(
            pepe_name: str,
            pepe_query_tool: PepeData = None,
            price_tool: PriceTool = None,
            pepe_details=None,
            fiat_enabled=False,
            loggers=None
    ):
        if loggers is None:
            loggers = {'data': logging.getLogger('data')}
        pepe_dispensers_data = pepe_query_tool.get_pepe_dispensers(pepe_name)
        pepe_dispensers_data = sorted(pepe_dispensers_data, key=lambda x: x['satoshirate'] / x['give_quantity'])

        pepe_image_url = 'pepes/images/' + pepe_query_tool._pepe_images[pepe_name]
        table_headers = ['Pepe', 'Stock', 'Pay', 'Receive'] if not fiat_enabled \
            else ['Pepe', 'Stock', 'USD', 'Pay', 'Receive']
        data_output = {
            'table_title': "BTC Dispensers",
            'table_headers': table_headers,
            'pepe_image_url': pepe_image_url,
            'rows': []
        }
        for i, pepe_dispenser_data in enumerate(pepe_dispensers_data):
            row_values = {
                'pepe_url': f"/{pepe_name}" + f"?d={i}",
                'pepe_image_url': pepe_image_url,
                'address': pepe_dispenser_data['source'],
                'address_truncated': pepe_dispenser_data['source'][:6] + '...',
                'stock': Formats.pepe_quantity_str(
                    pepe_dispenser_data['give_remaining'], pepe_details['divisible']
                ),
                'usd_value': price_tool.convert_satoshis_to_usd(pepe_dispenser_data['satoshirate']),
                'pay': Formats.satoshis_to_str(pepe_dispenser_data['satoshirate']),
                'pay_btc': f"{pepe_dispenser_data['satoshirate'] / 10 ** 8:.8f}",
                'receive': Formats.pepe_quantity_str(pepe_dispenser_data['give_quantity'], pepe_details['divisible']),
                'fiat_enabled': fiat_enabled,
                'xchain_tx_url': f"https://xchain.io/tx/{pepe_dispenser_data['tx_hash']}"
            }
            data_output['rows'].append(row_values)
        loggers['data'].info(f"Search results data: {pformat(data_output)}")
        return data_output


def get_pepe_markets(pepe_name: str, btc_price, xcp_price, pepecash_price):
    pepe_page_data = PepePage().create(pepe_name, loggers=loggers)

    data_set = {
        'dispensers': [],
        'xcp': {
            'buy': [],
            'sell': []
        },
        'pepecash': {
            'buy': [],
            'sell': []
        }
    }
    # dispenser_prices
    for pepe_dispenser in pepe_page_data['pepe_dispensers']['rows']:
        data_set['dispensers'].append({
            'price': float(pepe_dispenser['pay_btc']) / float(pepe_dispenser['receive'].replace(',','')),
            'id': pepe_dispenser['xchain_tx_url'].split('/')[-1]
        })
    for base_asset in ['xcp', 'pepecash']:
        for trade_type in ['buy', 'sell']:
            key = f"pepe_{base_asset}_orders"
            for trade_data in pepe_page_data[key][trade_type]['orders']:
                if base_asset == 'xcp':
                    price = xcp_price / btc_price * float(trade_data['pepe_price'].replace(',',''))
                else:
                    price = pepecash_price / btc_price * float(trade_data['pepe_price'].replace(',',''))
                data_set[base_asset][trade_type].append({
                    'price': price,
                    'id': trade_data['xchain_tx_url'].split('/')[-1]
                })
    # return pepe_page_data
    return data_set


def find_buy_opportunities(data_set: dict):
    try:
        opportunities = []
        for base_asset in ['xcp', 'pepecash']:
            for buy_trade in data_set[base_asset]['buy']:
                for target_asset in ['xcp', 'pepecash', 'dispensers']:
                    if target_asset == 'dispensers':
                        target_list = data_set[target_asset]
                    else:
                        target_list = data_set[target_asset]['sell']
                    for sell_trade in target_list:
                        # print(f"Testing:\n Buy: {buy_trade}\n to Sell:{sell_trade}\n")
                        if sell_trade['price'] < buy_trade['price']:
                            # print(True)
                            opportunities.append(sell_trade)
                        # else:
                        # print(False)
    except ZeroDivisionError:
        return []
    return opportunities


db_connection = DBConnector()
pepe_query_tool = PepeData(db_connection)
# pepe_names = pepe_query_tool.get_pepe_names()
pepe_page_data = PepePage().create('LEANPEPE', loggers=loggers)
pprint(pepe_page_data)
# price_tool = PriceTool(db_connection=db_connection)
# pepe_names = pepe_query_tool.get_pepe_names()
# btc_price = price_tool.get_btc_rate()
# pepecash_price = price_tool.get_pepecash_rate()
# xcp_price = price_tool.get_xcp_rate()
#
# i = pepe_names.index('XCP') + 1
# for i in range(i, len(pepe_names)):
#     print(pepe_names[i], end=": ")
#     data_set = get_pepe_markets(pepe_names[i], btc_price, xcp_price, pepecash_price)
#     # pprint(data_set)
#     print(f"{find_buy_opportunities(data_set)}")
