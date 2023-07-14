import requests
import json

# Make a GET request to the /sse endpoint
response = requests.get("http://51.132.13.113:8001/monitor_checkout_transactions", stream=True)
# response = requests.get("http://0.0.0.0:8001/check_validation_status", stream=True)

# Check if the request was successful
if response.status_code == 200:
    # Iterate over the server-sent events
    for chunk in response.iter_content(chunk_size=None):
        # Process the received event data
        if chunk:
            chunk_str = chunk.decode()
            # Extract the JSON data from the string
            json_start = chunk_str.find("{")  # Find the starting index of the JSON data
            json_data = chunk_str[json_start:]  # Extract the JSON data
            # Convert the JSON data to a dictionary
            dict_data = json.loads(json_data)
            print(dict_data)
else:
    print("Failed to establish SSE connection")




import requests
import json

url = "51.132.13.113:8001/update_transaction_checkout_status"

payload = json.dumps({})
headers = {
  'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE2OTAzNTM1OTYsImlhdCI6MTY4Nzc2MTU5Niwic3ViIjoiYWRtaW4ifQ.-g-wqdi4EcE6PfTfHH0_4sdJH5Fmn-A-9UIYxkcyCfY',
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)


# class CheckoutUpdate:

#     def __init__(self) -> None:
#         self.checkout_update = None
#         self.response = requests.get("http://51.132.13.113:8001/monitor_checkout_transactions", stream = True)

#     def check_response_status(self):
#         # Check if the request was successful
#         if self.response.status_code == 200:
#             # Iterate over the server-sent events
#             for chunk in self.response.iter_content(chunk_size = None):
#                 # Process the received event data
#                 if chunk:
#                     chunk_str = chunk.decode()
#                     # Extract the JSON data from the string
#                     json_start = chunk_str.find("{")  # Find the starting index of the JSON data
#                     json_data = chunk_str[json_start:]  # Extract the JSON data
#                     # Convert the JSON data to a dictionary
#                     self.checkout_update = json.loads(json_data)
#                     print(self.checkout_update)
#         else:
#             print("Failed to establish SSE connection")            


# headers = {
#     'Content-Type': 'application/json',
# }

# params = {
#     'transaction_id': '138',
# }

# json_data = {}

# response = requests.post(
#     'http://0.0.0.0:8001/update_transaction_validation_status',
#     params=params,
#     headers=headers,
#     json=json_data,
# )