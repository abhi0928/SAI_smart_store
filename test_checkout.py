import requests
import json
import pickle
import ast

class CheckoutUpdate:

    def __init__(self) -> None:
        self.checkout_update = None
        # Make a GET request to the /sse endpoint
        self.response = requests.get("http://51.132.13.113:8001/monitor_checkout_transactions", stream = True)
        self.status_file = open('checkout_status.pkl', 'wb')
        pickle.dump({}, self.status_file)
        self.status_file.close()
        self.validation_file = open('validation_status.pkl', 'wb')
        pickle.dump({}, self.validation_file)
        self.validation_file.close()


    def check_response_status(self):
        # Check if the request was successful
        if self.response.status_code == 200:
            # Iterate over the server-sent events
            for chunk in self.response.iter_content(chunk_size = None):
                # Process the received event data
                if chunk:
                    chunk_str = chunk.decode()
                    # Extract the JSON data from the string
                    json_start = chunk_str.find("{")  # Find the starting index of the JSON data
                    json_data = chunk_str[json_start:]  # Extract the JSON data
                    # Convert the JSON data to a dictionary
                    self.checkout_update = json.loads(json_data)
                    print(self.checkout_update)
                    with open('checkout_status.pkl', 'wb') as f:
                        # pickle.dumps(ast.literal_eval(self.checkout_update), f)
                        pickle.dump(self.checkout_update, f)
                    break
        else:
            print("Failed to establish SSE connection")


if __name__ == "__main__":

    checkout = CheckoutUpdate()
    checkout.check_response_status()