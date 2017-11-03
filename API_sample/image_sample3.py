########### Python 3.2 #############
import http.client, urllib.request, urllib.parse, urllib.error, base64
#from zhconv import zhconv
from hanziconv import HanziConv


headers = {
    # Request headers
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': 'a8d721a6ec1749e6a6efe7272c1e9f40',
}

params = urllib.parse.urlencode({
    # Request parameters
    'visualFeatures': 'Categories,Tags,Description',
    'details': 'Landmarks',
    'language': 'en',
})
#body = "{'url':'http://dpk.bantenprov.go.id/upload/articles/perpustakaan-yang-nyaman.jpg'}"
body = "{'url':'https://api.telegram.org/file/bot440630960:AAGUQskfKm7f6n2tKxb8t15BU7FHs3nAnNY/photos/file_21.jpg'}"
try:
    conn = http.client.HTTPSConnection('westcentralus.api.cognitive.microsoft.com')
    conn.request("POST", "/vision/v1.0/analyze?%s" % params, body, headers)
    response = conn.getresponse()
    data = response.read()
    print(HanziConv.toTraditional(data.decode('utf-8')))
    conn.close()
except Exception as e:
    print("[Errno {0}] {1}".format(e.errno, e.strerror))

####################################