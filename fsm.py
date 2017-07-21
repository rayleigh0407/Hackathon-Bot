from transitions.extensions import GraphMachine

import urllib.request
import re
import os
import apiai
import xml.etree.ElementTree as ET
import json

from asrapi import SpeechAPISample
import argparse
import time
import telegram

getVoice_baseURL = "https://api.telegram.org/bot440630960:AAGUQskfKm7f6n2tKxb8t15BU7FHs3nAnNY/"
Voice_pathURL = "https://api.telegram.org/file/bot440630960:AAGUQskfKm7f6n2tKxb8t15BU7FHs3nAnNY/"
global reply_text

def init_message():
    text =  "welcome\n" + \
            "查詢\n" + \
            "輸入\n"
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
            file_obj = urllib.request.urlopen(getVoice_baseURL + "getFile?file_id=" + voice['file_id']).read()
            get_path = re.split(b'"file_path"',file_obj)
            temp = re.findall(r'".*"',get_path[1].decode("utf-8"))
            file_path = re.sub(r'"','',temp[0])

            ### download file
            print(Voice_pathURL + file_path)
            urllib.request.urlretrieve(Voice_pathURL + file_path, "voice/sound.oga")

            ### Porting .oga to .wav
            os.system("ffmpeg -y -i voice/sound.oga -ar 16000 -c:a pcm_f32le voice/out.wav")

            ### translate voice
            url = "https://tw.olami.ai/cloudservice/api"
            appKey = "1a869a6aeae647c4aa346a6789523102"
            appSecret = "96361ffe6674470e9cc35cfded15b86d"
            audioFilePath = "voice/out.wav"
            compressed = True

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
            index1 = responseString.find("result")
            index2 = responseString.find("speech")
            responseString = responseString[index1+9:index2-3]
            
            output = intent_parser(responseString)
            output = output['result']['fulfillment']['speech']
            print(output)
            
            reply_text = output
        ## text input
        elif update.message.text != None:
            reply_text = update.message.text
        ## no input
        else:
            reply_text = 'no input'
    else:
        reply_text = 'no input'

    ### translate


    return reply_text

class TocMachine(GraphMachine):
    def __init__(self, **machine_configs):
        self.machine = GraphMachine(
            model = self,
            **machine_configs
        )

    def bot_init(self, update):
        if update.message != None:
            text = update.message.text
        else:
            text = 'no input'
       
        if text == '/start':
            reply_word = init_message()
            update.message.reply_text(reply_word)
            return True
        else:
            return False

    def is_going_to_translate(self, update):
        global reply_text
        reply_text = message_config(update)
        return reply_text != 'no input'

    def on_enter_init(self, update):
        update.message.reply_text("in init")
        return 0

    def on_exit_init(self, update):
        return 0

    def on_enter_translate(self, update):
        if reply_text != 'no input':
            update.message.reply_text("you say : " + reply_text)
        if reply_text == 'report':
            self.report(update)
        elif reply_text == 'query':
            self.query(update)
        else:
            self.again(update)
    
    def on_exit_translate(self, update):
        print("Leaving translate state\n")


    def on_enter_state1(self, update):
        update.message.reply_text("輸入啥")
        self.go_back(update)

    def on_exit_state1(self, update):
        print('Leaving state1')





    def on_enter_state2(self, update):
        update.message.reply_text("查啥")
        self.go_back(update)

    def on_exit_state2(self, update):
        print('Leaving state2')
