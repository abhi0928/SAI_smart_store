
import requests
import json
import uuid
from datetime import datetime
import ast
import pickle

def get_transaction_id():
    transaction_id = str(uuid.uuid4()).split('-')[0]
    url = "http://51.132.13.113:8001/add_transactions"

    payload = json.dumps({
        "email": "admin",
        "name": transaction_id,
        "status": 0,
        "datetime": str(datetime.now())
        })
    headers = {
            'Content-Type': 'application/json'
            }

    response = requests.request("POST", url, headers = headers, data = payload)
    tran_id = ast.literal_eval(response.text)
    return tran_id["transaction_id"]

def add_transactions(tran_id, item_id, quantity):
    url = "http://51.132.13.113:8001/add_transaction_items"

    payload = json.dumps({
        "transaction_id": int(tran_id),
        "item_id": item_id,
        "quantity": int(quantity),
        "datetime": str(datetime.now())
            })
    headers = {
        'Content-Type': 'application/json'
        }

    response = requests.request("POST", url, headers = headers, data = payload)
    print(f"item {item_id} successfully added")

def update_transaction_validation_status(tran_id):
    url = f"http://51.132.13.113:8001/update_transaction_validation_status?transaction_id={tran_id}"
    payload = json.dumps({})
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers = headers, data = payload)

    print("Transaction Validation successfull")
    print(response.text)




