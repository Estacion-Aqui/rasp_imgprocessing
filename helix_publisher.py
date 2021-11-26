import json
import requests

class HelixPublisher:

    head = {"Content-Type": "application/json", "fiware-service":"helixiot", "fiware-servicepath":"/"}

    def send_message(self, id, attribute):
        url = f"http://34.151.219.62:1026/v2/entities/{id}/attrs"
        
        print(attribute)

        response = requests.post(url, data=json.dumps(attribute), headers=self.head)
        print(response)
