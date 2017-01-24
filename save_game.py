import configparser
import hashlib
import json
import os.path
import six
import sys

import socketIO_client

if sys.version_info >= (3, 0):
    six.b = lambda s: s.encode()

waitTime = 0.5
indent = 2

historyGames = []
messageHistory = None

names = ['Alice', 'Bob', 'Cathy', 'Donald', 'Emily']

def on_message(*args):
    global position
    if not args or isinstance(args[0], bytes):
        return

    mtype = args[0]['type']
    if mtype == 'game_history':
        historyGames.append(args[0]['resp']['id'])
    if messageHistory is not None:
        if mtype in ['game_start', 'init', 'notify']:
            message = args[0]
            if mtype == 'init':
                numPlayers = len(message['resp']['names'])
                message['resp']['names'] = names[:numPlayers]
            messageHistory.append(message)


user = configparser.ConfigParser()
user.read('user.ini')

conn = socketIO_client.SocketIO('keldon.net', 32221)
conn.on('message', on_message)

username = user['USER']['username']
password = user['USER']['password']
passSha = hashlib.sha256(b'Hanabi password ' + password.encode()).hexdigest()

try:
    login = {'username': username, 'password': passSha}
    conn.emit('message', {'type': 'login', 'resp': login})
    conn.wait(seconds=1)

    while True:
        print('Download which game? (Press 0 to list games)')
        v = input('--> ')

        try:
            id = int(v)
        except ValueError:
            break

        if id == 0:
            print('Game IDs:')
            for id in historyGames:
                print(id)
        elif id not in historyGames:
            print('Game does not exist or you did not play in it')
        else:
            messageHistory = []
            conn.emit('message', {'type': 'start_replay', 'resp': {'id': id}})
            conn.wait(seconds=waitTime)
            conn.emit('message', {'type': 'hello', 'resp': {}})
            conn.emit('message', {'type': 'ready', 'resp': {}})
            conn.wait(seconds=waitTime)
            conn.emit('message', {'type': 'abort', 'resp': {}})
            conn.wait(seconds=waitTime)

            if not os.path.isdir('games'):
                os.mkdir('games')
            filepath = os.path.join('games', str(id) + '.json')
            with open(filepath, 'w') as fp:
                json.dump(messageHistory, fp, indent=indent)
            print('Saved game to ' + filepath)

            messageHistory = None
finally:
    conn.disconnect()
