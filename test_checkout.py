import requests
import json

# Make a GET request to the /sse endpoint
response = requests.get("http://0.0.0.0:8001/monitor_checkout_transactions", stream=True)
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