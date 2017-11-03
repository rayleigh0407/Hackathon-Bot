import http.client, urllib.request, urllib.parse, urllib.error, base64
from hanziconv import HanziConv 
import re

headers = {
    # Request headers
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': 'a8d721a6ec1749e6a6efe7272c1e9f40',
}

params = urllib.parse.urlencode({
    # Request parameters
    'visualFeatures': 'tags',
    'details': 'Landmarks',
    'language': 'zh',
})
body = "{'url':'http://www.bocach.gov.tw/files/508_1031008_%E9%96%8B%E6%9E%B6%E9%96%B1%E8%A6%BD%E5%8D%80.JPG'}"
try:
    conn = http.client.HTTPSConnection('westcentralus.api.cognitive.microsoft.com')
    conn.request("POST", "/vision/v1.0/analyze?%s" % params, body, headers)
    response = conn.getresponse()
    img_result = HanziConv.toTraditional(response.read().decode('utf-8'))
    conn.close()
except Exception as e:
    print("[Errno {0}] {1}".format(e.errno, e.strerror))

print(img_result)


## sentence recognition

headers = {
    # Request headers
    'Ocp-Apim-Subscription-Key': '9cb6cd5e1b984583a4c656cd4c320201',
}

params = urllib.parse.urlencode({
    'model': 'title',
    'text': '你家火災',
    'order': '5',
    'maxNumOfCandidatesReturned': '5',
})

try:
    conn = http.client.HTTPSConnection('westus.api.cognitive.microsoft.com')
    conn.request("POST", "/text/weblm/v1.0/breakIntoWords?%s" % params, "{body}", headers)
    response = conn.getresponse()
    lan_result = response.read().decode('utf-8')
    conn.close()
except Exception as e:
    print("[Errno {0}] {1}".format(e.errno, e.strerror))



flag = False
print(lan_result)
while True:
    index3 = img_result.find("name")
    index4 = img_result.find("confidence")
    if index3 < 0:
        break
    img_parse = img_result[index3+7:index4-3]
    if index4 - index3 > 50:
        img_result = img_result[index3+4:]
        continue
    img_result = img_result[index4+5:]
    lan_result_parse = lan_result
    while True:
        index1 = lan_result_parse.find("words")
        index2 = lan_result_parse.find("probability")
        if index1 < 0:
            break;
        lan_parse = lan_result_parse[index1+8:index2-3]
        lan_result_parse = lan_result_parse[index2+11:]
        print(img_parse + ' vs ' + lan_parse)
        search_result = re.search(img_parse, lan_parse)
        print(search_result)
        if search_result:
            flag = True
print(flag)

