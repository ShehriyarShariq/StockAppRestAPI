import pandas as pd
import math

import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    cred = credentials.Certificate('./key.json')
    firebase_admin.initialize_app(cred)

firestore_db = firestore.client()

stocksData = pd.read_json('./nse_stocks.json')

stocks = stocksData.to_dict('records')

MAX_ALLOWED_WRITES = 500

ranges = [[MAX_ALLOWED_WRITES * i, (i * MAX_ALLOWED_WRITES) + MAX_ALLOWED_WRITES] for i in range(math.ceil(len(stocks) / MAX_ALLOWED_WRITES))]

if ranges[-1][1] > len(stocks):
    ranges[-1][1] = len(stocks)

print(ranges)

for selectedRange in ranges:
    batch = firestore_db.batch()
    for stock in stocks[selectedRange[0]:selectedRange[1]]:
        batch.set(firestore_db.collection(u'stocks').document(), {
            'code': stock['Code'],
            'name': stock['Name'],
            'currency': stock['Currency'],
            'exchange': stock['Exchange'],
        })
    batch.commit()