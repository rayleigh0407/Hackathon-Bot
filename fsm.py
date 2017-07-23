from transitions.extensions import GraphMachine

import http.client, urllib.request, urllib.parse, urllib.error, base64
import re
import os
import apiai
import xml.etree.ElementTree as ET
import json
from hanziconv import HanziConv
from imgurpython import ImgurClient
import MySQLdb

from asrapi import SpeechAPISample
import argparse
import time
import telegram
import datetime


getFile_baseURL = "https://api.telegram.org/bot440630960:AAGUQskfKm7f6n2tKxb8t15BU7FHs3nAnNY/"
file_pathURL = "https://api.telegram.org/file/bot440630960:AAGUQskfKm7f6n2tKxb8t15BU7FHs3nAnNY/"
imgur_client_id = 'c797238e516a3f1'
imgur_client_secret = '0a7c0fdbfd3d4db9eeae9fba15f22931a3edde4c'
global reply_text
global lat, lng
global img_result
global database
global insert_data

def start_message():
    text =  "歡迎使用即時資訊回報機器人\n"
    return text

def init_message():
    text =  "想要知道附近發生什麼事\n可以詢問我～\n(e.g. 我想知道附近發生什麼事！)\n.\n" + \
            "想要告訴我你所在地點發生什麼事\n也可以告訴我～\n(e.g. 我要回報！)\n"
    return text

def intent_parser(input):
    client = apiai.ApiAI('8a96e6d79c0e48f49f626a74797bdcce')
    request = client.text_request()
    request.query = input
    response = request.getresponse()
    return json.loads(response.read().decode())


def message_config(update):
    if update.message != None:
        
        ## voice input
        if update.message.voice != None:

            ### get `file_id` and `file_path`
            voice = update.message.voice
            file_obj = urllib.request.urlopen(getFile_baseURL + "getFile?file_id=" + voice['file_id']).read()
            get_path = re.split(b'"file_path"',file_obj)
            temp = re.findall(r'".*"',get_path[1].decode("utf-8"))
            file_path = re.sub(r'"','',temp[0])

            ### download file
            print(file_pathURL + file_path)
            urllib.request.urlretrieve(file_pathURL + file_path, "voice/sound.oga")

            ### Porting .oga to .wav
            os.system("ffmpeg -y -i voice/sound.oga -ar 16000 -c:a pcm_s16le voice/out.wav")

            ### translate voice
            url = "https://tw.olami.ai/cloudservice/api"
            appKey = "1a869a6aeae647c4aa346a6789523102"
            appSecret = "96361ffe6674470e9cc35cfded15b86d"
            audioFilePath = "voice/out.wav"
            compressed = False

            asrApi = SpeechAPISample()
            asrApi.setLocalization(url)
            asrApi.setAuthorization(appKey, appSecret)     

            '''Start sending audio file for recognition'''
            #print("\n----- Test Speech API, seq=nli,seg -----\n")
            #print("\nSend audio file... \n");
            responseString =  asrApi.sendAudioFile(asrApi.API_NAME_ASR, 
                    "nli,seg", True, audioFilePath, compressed)
            #print("\n\nResult:\n\n" , responseString, "\n")

            ''' Try to get recognition result if uploaded successfully.    
                We just check the state by a lazy way :P , you should do it by JSON.'''
            if ("error" not in responseString.lower()): 
                #print("\n----- Get Recognition Result -----\n")
                time.sleep(1) #delay for 1 second
                ''' Try to get result until the end of the recognition is complete '''
                while (True):
                    responseString = asrApi.getRecognitionResult(
                            asrApi.API_NAME_ASR, "nli,seg")
                    #print("\n\nResult:\n\n" , responseString ,"\n")

                    #print(responseString)
                    ''' Well, check by lazy way...again :P , do it by JSON please. '''
                    if ("\"final\":true" not in responseString.lower()): 
                        #print("The recognition is not yet complete.")
                        if ("error" in responseString.lower()): 
                            break
                        time.sleep(2) #delay for 2 second
                    else: 
                        break

            #print("\n\n")
            index1 = responseString.find("result")
            index2 = responseString.find("speech")
            responseString = responseString[index1+9:index2-3]

            reply_text = responseString
        ## text input
        elif update.message.text != None:
            reply_text = update.message.text
        ## no input
        else:
            reply_text = 'no input'
    else:
        reply_text = 'no input'

    print("command : " + reply_text)

    return reply_text

def insert_data_clean():
    global insert_data
    insert_data = dict([('ID', 0), 
                        ('time', 'non'),
                        ('location', 'non'),
                        ('event', 'non'),
                        ('Lat', 0.0),
                        ('Lng', 0.0),
                        ('URL', 'non'),
                        ('turn_in', 0),
                        ('category','non')])


    db = MySQLdb.connect("127.0.0.1",    # your host, usually localhost
                     "f74036124",         # your username
                     "eJdFEncbpxcQEdbe",  # your password
                     "f74036124")        # name of the data base
    cur = db.cursor()
    cur.execute("SELECT * FROM `irp_report_table`")
    for row in cur.fetchall():
        insert_data['ID'] = insert_data['ID'] + 1

    db.close()
    return 0

class TocMachine(GraphMachine):
    bot = None
    def __init__(self, b, **machine_configs):
        self.bot = b
        self.machine = GraphMachine(
            model = self,
            **machine_configs
        )

    def bot_init(self, update):

        insert_data_clean()



        if update.message != None:
            text = update.message.text
        else:
            text = 'no input'
       
        if text == '/start':
            reply_word = start_message() + init_message()
            update.message.reply_text(reply_word)
            return True
        else:
            return False

    def is_going_to_translate(self, update):
        global reply_text
        reply_text = 'no input'
        reply_text = message_config(update)
        
        ### translate
        if reply_text != 'no input':
            output = intent_parser(reply_text)
            output = output['result']['fulfillment']['speech']
            print(output)
            reply_text = output
        return True

    def is_going_to_get_gps(self, update):
        if update['message']['location']:
            global lat, lng
            global insert_data
            lat = update['message']['location']['latitude']
            lng = update['message']['location']['longitude']
            
            # debug
            insert_data['Lat'] = lat
            insert_data['Lng'] = lng

            #self.bot.sendLocation(update.message.chat.id, lat, lng)
            
            return True
        else:
            update.message.reply_text('請傳給我你的地址')
            return False

    def is_going_to_get_photo(self, update):

        global insert_data

        if update.message.photo:
            global img_result
            pic = update.message.photo[len(update.message.photo) - 1]['file_id']
            print(pic)
            file_obj = urllib.request.urlopen(getFile_baseURL + "getFile?file_id=" + pic).read()
            get_path = re.split(b'"file_path"',file_obj)
            temp = re.findall(r'".*"',get_path[1].decode("utf-8"))
            file_path = re.sub(r'"','',temp[0])

            ### download image
            urllib.request.urlretrieve(file_pathURL + file_path, "img/now.jpg")

            ### picture analysis
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

            # picture path
            print(file_pathURL + file_path)
            body = "{'url':'" + file_pathURL + file_path + "'}"
            
            try:
                conn = http.client.HTTPSConnection('westcentralus.api.cognitive.microsoft.com')
                conn.request("POST", "/vision/v1.0/analyze?%s" % params, body, headers)
                response = conn.getresponse()
                data = response.read()
                img_result = HanziConv.toTraditional(data.decode('utf-8'))
                reply_text = img_result
                conn.close()
            except Exception as e:
                print("[Errno {0}] {1}".format(e.errno, e.strerror))

            # debug
            print(img_result)

            return True
        else:
            update.message.reply_text("請上傳事件的照片")
            return False

    def is_going_to_get_event(self, update):
        flag = False
        global img_result
        global reply_text
        global insert_data

        reply_text = message_config(update)

        if reply_text != 'no input':
            text = reply_text
            
            headers = {
                # Request headers
                'Ocp-Apim-Subscription-Key': '9cb6cd5e1b984583a4c656cd4c320201',
            }

            params = urllib.parse.urlencode({
                'model': 'title',
                'text': text,
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

            temp_img_result = img_result
            while True:
                index3 = temp_img_result.find("name")
                index4 = temp_img_result.find("confidence")
                if index3 < 0:
                    break
                img_parse = temp_img_result[index3+7:index4-3]
                if index4 - index3 > 50:
                    temp_img_result = temp_img_result[index3+4:]
                    continue
                temp_img_result = temp_img_result[index4+5:]
                lan_result_parse = lan_result
                while True:
                    index1 = lan_result_parse.find("words")
                    index2 = lan_result_parse.find("probability")
                    if index1 < 0:
                        break
                    lan_parse = lan_result_parse[index1+8:index2-3]
                    lan_result_parse = lan_result_parse[index2+11:]
                    print(img_parse + ' vs ' + lan_parse)
                    search_result = re.search(img_parse, lan_parse)
                    print(search_result)
                    if search_result:
                        flag = True


            # debug
            if flag:


                insert_data['event'] = reply_text
                insert_data['category'] = 'option4'

                client = ImgurClient(imgur_client_id, imgur_client_secret)
                upload_im = client.upload_from_path("img/now.jpg", None, True)
                insert_data['URL'] = upload_im['link']
                
                date = datetime.datetime.now()
                y = str(date.year)
                m = str(date.month)
                d = str(date.day)
                date = y + "-" + m + "-" + d
                insert_data['time'] = date
                insert_data['turn_in'] = 0

                text = urllib.request.urlopen("https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(lat) + "%2C" + str(lng) + "&key=AIzaSyC0YHjxhTqUPSIQtCRRLPsKmYZ8NUmiX00&language=zh-TW").read().decode('utf-8')
                index3 = text.find("formatted_address")
                index4 = text.find("geometry")
                address_parse = text[index3 + 22:index4 - 13]
                insert_data['location'] = address_parse

                db = MySQLdb.connect("127.0.0.1",    # your host, usually localhost
                     "f74036124",         # your username
                     "eJdFEncbpxcQEdbe",  # your password
                     "f74036124",
                     charset="utf8")        # name of the data base

                cur = db.cursor()
                cur.execute("SET NAMES utf8")

                try:
                    print("INSERT INTO irp_report_table values ( NULL,'" + \
                            str(insert_data['time']) + "','" + \
                            str(insert_data['location']) + "','" + \
                            str(insert_data['event']) + "','" + \
                            str(insert_data['Lat']) + "','" + \
                            str(insert_data['Lng']) + "','" + \
                            str(insert_data['URL']) + "','" + \
                            str(insert_data['turn_in']) + "','" + \
                            str(insert_data['category']) + "' )")
                    '''print("""INSERT INTO irp_report_table values (NULL,%s,%s,%s,%s,%s,%s,%s,%s)""", 
                    (   insert_data['time'] , 
                        insert_data['location'], 
                        insert_data['event'], 
                        insert_data['Lat'], 
                        insert_data['Lng'], 
                        insert_data['URL'], 
                        insert_data['turn_in'], 
                        insert_data['category']))'''
                    cur.execute("INSERT INTO irp_report_table values ( NULL,'" + \
                            str(insert_data['time']) + "','" + \
                            str(insert_data['location']) + "','" + \
                            str(insert_data['event']) + "','" + \
                            str(insert_data['Lat']) + "','" + \
                            str(insert_data['Lng']) + "','" + \
                            str(insert_data['URL']) + "','" + \
                            str(insert_data['turn_in']) + "','" + \
                            str(insert_data['category']) + "')")
                    db.commit()
                    print("上傳完成\n")
                except:
                    print("upload error\n")
                    db.rollback()
                
            else:
                print("輸入錯誤\n")
                update.message.reply_text("這似乎與照片內的事件沒什麼關聯\n請重新輸入一次")

            return flag
        else:
            return False

    def on_enter_init(self, update):
        print("in init")
        return 0

    def on_exit_init(self, update):
        print("in init")
        return 0

    def on_enter_translate(self, update):
        if reply_text == 'report':
            update.message.reply_text("請依照指示進行回報")
            self.report(update)
        elif reply_text == 'query':
            update.message.reply_text("請依照指示進行查詢")
            self.query(update)
        else:
            update.message.reply_text(reply_text)
            self.again(update)
    
    def on_exit_translate(self, update):
        print("Leaving translate state\n")


    def on_enter_report(self, update):
        update.message.reply_text("請上傳地點")

    def on_exit_report(self, update):
        print('Leaving report')

    def on_enter_get_gps(self, update):
        update.message.reply_text("請上傳圖片")

    def on_exit_get_gps(self, update):
        print("Leaving gps")

    def on_enter_get_photo(self, update):
        update.message.reply_text("發生啥事")

    def on_exit_get_photo(self, update):
        print("Leaving photo")

    def on_enter_get_event(self, update):
        update.message.reply_text("感謝您的回報")
        update.message.reply_text(init_message())
        self.go_back(update)

    def on_exit_get_event(self, update):
        print("Leaving get event")        

    def on_exit_get_event(self, update):
        print("Leaving event")

    def on_enter_query(self, update):
        update.message.reply_text("請給我地址")

    def on_exit_query(self, update):
        print('Leaving query')

    def on_enter_query_result(self, update):
        update.message.reply_text("附近發生的事件：")
        db = MySQLdb.connect("127.0.0.1",    # your host, usually localhost
                     "f74036124",         # your username
                     "eJdFEncbpxcQEdbe",  # your password
                     "f74036124",
                     charset="utf8")        # name of the data base

        cur = db.cursor()
        cur.execute("SET NAMES utf8")

        lat_up = lat + 0.01
        lng_up = lng + 0.01
        lat_down = lat - 0.01
        lng_down = lng - 0.01

        condition = "Lat <= " + str(lat_up) + " AND Lat >= " + str(lat_down) + " AND Lng <= " + str(lng_up) + " AND Lng >= " + str(lng_down)
        # Use all the SQL you like
        cur.execute("SELECT * FROM irp_report_table WHERE " + condition)

        # print all the first cell of all the rows
        count = 0
        send_message = ""
        for row in cur.fetchall():
            count = count + 1
            send_message = str(count) + ".\n"
            send_message = send_message + "事件：" + row[3] + "\n"
            
            print("ID : " + str(row[0]))
            print("event : " + str(row[3]))
            print("Lat : " + str(row[4]))
            print("Lng : " + str(row[5]))
            #text = urllib.request.urlopen("https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(row[4]) + "%2C" + str(row[5]) + "&key=AIzaSyC0YHjxhTqUPSIQtCRRLPsKmYZ8NUmiX00&language=zh-TW").read().decode('utf-8')
            #index3 = text.find("formatted_address")
            #index4 = text.find("geometry")
            #address_parse = text[index3 + 22:index4 - 13]
            #insert_data['location'] = address_parse
            send_message = send_message + "位置：" + row[2] + "\n"
            send_message = send_message + "圖片（如果有上傳）及地圖在下方\n"
            update.message.reply_text(send_message)
            if row[6] != '':
                update.message.reply_text(row[6])
            self.bot.sendLocation(update.message.chat.id, row[4], row[5])


        db.close()             

        update.message.reply_text("搜尋完畢")
        update.message.reply_text(init_message())
        self.go_back(update)

    def on_exit_query_result(self, update):
        print('Leaving query result')
