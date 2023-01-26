from pprint import pprint
import requests

data = {
    'storeId': "AVJJry3fWe8X9AFavCy6XvE7bhE12QUJUuFTwR47mKGj",
    'checkoutDesc': "5 Days worth of advertising _PEPENAME_ at RarePepeWorld. First come, first serve. ",
    'price': "200",
    'currency': "USD",
    'checkoutQueryString': "rarepepeworld.com"
}

r = requests.post(
    'https://pay.rarepepeworld.com/api/v1/invoices',
    data=data
)

pprint(r)
print(r.text)
print(r.json)
print(r.content)
