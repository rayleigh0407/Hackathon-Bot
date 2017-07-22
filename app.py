import sys
from io import BytesIO

import urllib.request
import re

import telegram
from flask import Flask, request, send_file

from fsm import TocMachine

text = urllib.request.urlopen("http://127.0.0.1:4040").read()
url = re.search(b"https://([A-Za-z0-9]+)\.ngrok\.io", text)

API_TOKEN = '440630960:AAGUQskfKm7f6n2tKxb8t15BU7FHs3nAnNY'
WEBHOOK_URL = url.group(0).decode('utf-8') + '/hook'



app = Flask(__name__)
bot = telegram.Bot(token=API_TOKEN)
machine = TocMachine(
    bot,
    states=[
        'user',
        'init',
        'translate',
        'report',
        'query',
        'get_gps',
        'get_photo',
        'get_event',
        'query_result',
    ],
    transitions=[
        {
            'trigger': 'advance',
            'source': 'user',
            'dest': 'init',
            'conditions': 'bot_init'
        },
        {
            'trigger': 'advance',
            'source': 'init',
            'dest': 'translate',
            'conditions': 'is_going_to_translate'
        },
        {
            'trigger': 'again',
            'source': 'translate',
            'dest': 'init'
        },
        {
            'trigger': 'report',
            'source': 'translate',
            'dest': 'report'
        },
        ##  report stage 1: upload location
        {
            'trigger': 'advance',
            'source': 'report',
            'dest': 'get_gps',
            'conditions': 'is_going_to_get_gps'
        },
        ##  report stage 2: upload photo
        {
            'trigger': 'advance',
            'source': 'get_gps',
            'dest': 'get_photo',
            'conditions': 'is_going_to_get_photo'
        },
        ##  report stage 3: input event
        {
            'trigger': 'advance',
            'source': 'get_photo',
            'dest': 'get_event',
            'conditions': 'is_going_to_get_event'
        },
        {
            'trigger': 'query',
            'source': 'translate',
            'dest': 'query',
        },
        {
            'trigger': 'advance',
            'source': 'query',
            'dest': 'query_result',
            'conditions': 'is_going_to_get_gps'
        },
        {
            'trigger': 'go_back',
            'source': [
                'query_result',
                'get_event'
            ],
            'dest': 'init'
        }
    ],
    initial='user',
    auto_transitions=False,
    show_conditions=True,
)


def _set_webhook():
    status = bot.set_webhook(WEBHOOK_URL)
    if not status:
        print('Webhook setup failed')
        sys.exit(1)
    else:
        print('Your webhook URL has been set to "{}"'.format(WEBHOOK_URL))


@app.route('/hook', methods=['POST'])
def webhook_handler():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    machine.advance(update)
    # debug
    if machine.state == 'init':
        update.message.reply_text(update.message.chat.id)
        bot.sendLocation(update.message.chat.id, 25.0616, 121.5276)
    return 'ok'


@app.route('/show-fsm', methods=['GET'])
def show_fsm():
    byte_io = BytesIO()
    machine.graph.draw(byte_io, prog='dot', format='png')
    byte_io.seek(0)
    return send_file(byte_io, attachment_filename='fsm.png', mimetype='image/png')


if __name__ == "__main__":
    _set_webhook()
    app.run()
