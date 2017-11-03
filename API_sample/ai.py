import xml.etree.ElementTree as ET
import urllib.request
import apiai
import json

def intent_parser(input):
    client = apiai.ApiAI('8a96e6d79c0e48f49f626a74797bdcce')
    request = client.text_request()
    request.query = input
    response = request.getresponse()
    return json.loads(response.read().decode())

input_text = '回報'
output = intent_parser(input_text)
output = output['result']['fulfillment']['speech']
print(output)


