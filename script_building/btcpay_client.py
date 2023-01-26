import pickle
from pprint import pprint, pformat
import hashlib
import hmac
from random import randint

from btcpay import BTCPayClient

# client_store_file = "../rpw/static/data/btc_pay_client"
client_store_file = "../rpw/static/data/btc_pay_client_testing"


def create_pairing_object(pairing_code: str):
    out_file = open(client_store_file, 'wb')
    _client = BTCPayClient.create_client(host='https://pay.rarepepeworld.com', code=pairing_code)
    pickle.dump(_client, out_file)
    out_file.close()


def load_client_object():
    with open(client_store_file, 'rb') as in_file:
        _client = pickle.load(in_file)
    return _client


def test_hash():
    body = "{'deliveryId': 'TvzsdsxLedHVgwmoKmP8mk', 'webhookId': 'BwwCPGB9VQwTwndQsaRNmK', 'originalDeliveryId': '__test__f6f5d387-57d8-4131-9944-c9c030e78c71__test__', 'isRedelivery': False, 'type': 'InvoiceCreated', 'timestamp': 1634114447, 'storeId': 'AVJJry3fWe8X9AFavCy6XvE7bhE12QUJUuFTwR47mKGj', 'invoiceId': '__test__3b32aeb7-3ded-449b-8901-2e2585696e5b__test__'}"
    hash_str = "sha256=75cded29d1bfb6a5e737d4d29236c72a53c91877db9bcf8918fc1f1fe5d40a4d"
    secret = '2rNbyv7Aezgyf7oUmphQiEN4wTZJ'
    h = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    print(f'sha256={h}')
    print(hash_str)


def run():
    _client = load_client_object()
    pprint(_client.get_invoice(invoice_id='AaeW3yahWqtG1Kuc7NtLax'))


# create_pairing_object("x5BafHx")

client = load_client_object()

# invoice = client.get_invoice('A8XcdhAojJ534iDUQoxJjm')
# print(pformat(invoice))

order_id = f"__test__{randint(100_000, 999_999)}"
pepe_name = "PEPETHUGLIFE"
block_count = 720
item_code = f"AD_{block_count}"
post_data = {
    'order_id': order_id,
    'pepe_name': pepe_name,
    'block_count' : block_count
}
invoice_data = {"orderId": order_id,
                "currency": "USD",
                "itemCode": item_code,
                "itemDesc": f"5 Days worth of advertising for {pepe_name} at RarePepeWorld. First come, first serve.",
                "notificationUrl": 'http://rarepepeworld.com:55000/B28vk',
                "redirectURL": "http://rarepepeworld.com:55000/invoice",
                "posData": str(post_data),
                "price": "0.50"}

payload = client.create_invoice(invoice_data)
print(pformat(payload))
print(payload['posData'])
