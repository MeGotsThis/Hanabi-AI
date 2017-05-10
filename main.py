import argparse
import configparser
import getpass
import hashlib
import importlib
import os.path
import sys

from collections import ChainMap
from typing import Any, Dict, List, Optional, Type

import socketIO_client
import six

from bot.bot import Bot
from game import Game
from enums import Variant

_errorObj: object = object()

six.b = lambda s: s.encode()

waitTime: float = 0.1
tables: Dict[int, dict] = {}
currentTableId: Optional[int] = None
currentTable: Optional[dict] = None
currentTablePosition: Optional[int] = None
tablePlayers: List[str] = []
readyToStart: bool = False
game: Optional[Game] = None
conn: socketIO_client.SocketIO
botconfig: configparser.ConfigParser
botCls: Type[Bot]


def on_message(*args):
    global currentTable, currentTableId, currentTablePosition
    global game, readyToStart
    if not args or isinstance(args[0], bytes):
        return
    mtype: str = args[0]['type']
    if mtype in ['hello', 'advanced']:
        args[0]['resp'] = {}
    data: dict = args[0]['resp']

    if mtype == 'denied':
        print(data['reason'])
        sys.exit()
    elif mtype == 'error':
        print(data['error'])
    elif mtype == 'table':
        tables[data['id']] = data
    elif mtype == 'table_gone':
        if data['id'] in tables:
            del tables[data['id']]
    elif mtype == 'joined':
        currentTableId = data['table_id']
    elif mtype == 'left':
        print('Game Terminated')
        currentTable = None
        currentTableId = None
        game = None
    elif mtype == 'table_ready':
        readyToStart = data['ready']
    elif mtype == 'game':
        currentTable = data
        tablePlayers.clear()
    elif mtype == 'game_player':
        tablePlayers.append(data['name'])
        if data['you']:
            currentTablePosition = data['index']
    elif mtype == 'game_start':
        print('Game Started: ' + tables[currentTableId]['name'])
        conn.emit('message', {'type': 'hello', 'resp': {}})
    elif mtype == 'init':
        kwargs = botconfig['BOT']
        if botconfig['BOT']['bot'] in botconfig:
            kwargs = ChainMap(botconfig[botconfig['BOT']['bot']],
                              botconfig['BOT'])
        game = Game(conn, Variant(data['variant']), data['names'],
                    data['seat'], botCls, **kwargs)
        print('Game Loaded')
        conn.emit('message', {'type': 'ready', 'resp': {}})
    elif mtype in ['hello', 'user', 'user_left', 'chat',
                   'game_history', 'history_detail', 'game_error',
                   'connected']:
        pass
    elif game is not None:
        game.received(mtype, data)
        if mtype == 'notify' and data['type'] == 'game_over':
            game = None
    elif mtype == 'notify' and data['type'] == 'reveal':
        pass
    elif mtype == 'action':
        pass
    else:
        print(mtype, data)
        raise Exception()


def int_input(prompt: str='-->', *, min=None, max=None, error=_errorObj
              ) -> Any:
    while True:
        try:
            i = int(input(prompt))
            if min is not None and i < min:
                raise ValueError()
            if max is not None and i > max:
                raise ValueError()
            return i
        except ValueError:
            if error is not _errorObj:
                return error


def run(username: str, password: str, botIni: str='bot.init') -> None:
    global conn, botconfig, botCls
    botconfig = configparser.ConfigParser()
    botconfig.read(botIni)

    print('Loading Bot AI')
    botModule = importlib.import_module(botconfig['BOT']['bot'] + '.bot')
    botCls = botModule.Bot  # type: ignore
    print('Loaded ' + botCls.BOT_NAME)

    conn = socketIO_client.SocketIO('keldon.net', 32221)
    conn.on('message', on_message)

    print('Connected to keldon.net')


    passBytes = b'Hanabi password ' + password.encode()
    passSha: str
    passSha = hashlib.sha256(passBytes).hexdigest()

    try:
        login: dict = {'username': username, 'password': passSha}
        conn.emit('message', {'type': 'login', 'resp': login})
        conn.wait(seconds=1)

        i: int = 0
        d: dict
        t: int
        id: int
        table: dict
        while True:
            print()
            print('What would you like to do?')
            print('(1) Create a table')
            print('(2) Join a table')
            print('(3) Rejoin a game')
            print('(0) Quit')
            try:
                i = int(input('--> '))
                if i < 1 or i > 3:
                    raise ValueError()
            except ValueError:
                break

            conn.wait(seconds=waitTime)

            if i in [1, 2]:
                if i == 1:
                    name = input('Game Name --> ')
                    max_players = int_input('Max Players (2 - 5) --> ',
                                            min=2, max=5)
                    print('Variant')
                    for variant in Variant:
                        print('({}) {}'.format(variant.value,
                                               variant.full_name))
                    variant = int_input(min=0, max=len(Variant) - 1)
                    print('Allow Spectators? (y or 1 for yes)')
                    allow_spec: bool = input('--> ') in ['1', 'y', 'Y']
                    d = {'type': 'create_table',
                         'resp': {'name': name,
                                  'max': max_players,
                                  'variant': variant,
                                  'allow_spec': allow_spec}}
                    conn.emit('message', d)
                else:
                    while True:
                        print('Join a table')
                        print('(Blank) Refresh')
                        print('''(    0) Don't Join A Table''')
                        for id, table in sorted(tables.items()):
                            if table['running']:
                                continue
                            print('({:>5}) {}, Players: {}/{}, Variant: '
                                  '{}'.format(
                                id, table['name'], table['num_players'],
                                table['max_players'],
                                Variant(table['variant']).full_name))
                        try:
                            t = int(input('--> '))
                        except ValueError:
                            conn.wait(seconds=waitTime)
                            continue
                        if t == 0:
                            break
                        conn.wait(seconds=waitTime)
                        if t not in tables:
                            print('Table does not exist')
                            continue
                        if tables[t]['running']:
                            print('Game already started')
                            continue
                        if tables[t]['joined']:
                            d = {'type': 'reattend_table',
                                 'resp': {'table_id': t}}
                        else:
                            d = {'type': 'join_table',
                                 'resp': {'table_id': t}}
                        conn.emit('message', d)
                        break

                conn.wait(seconds=waitTime)
                while currentTableId in tables and game is None:
                    conn.wait(seconds=waitTime)
                    if currentTableId in tables and game is None:
                        print('Current Players', tablePlayers)
                        print('(Blank) Refresh')
                        print('(0) Abandon Game')
                        if tables[currentTableId]['owned'] and readyToStart:
                            print('(1) Start Game')
                        try:
                            i = int(input('--> '))
                            if i == 0:
                                conn.emit('message', {'type': 'leave_table',
                                                      'resp': {}})
                                break
                            if (tables[currentTableId]['owned']
                                    and readyToStart):
                                if i == 1:
                                    d = {'type': 'start_game', 'resp': {}}
                                    conn.emit('message', d)
                                    break
                        except:
                            conn.wait(seconds=waitTime)
                            continue
                conn.wait(seconds=waitTime)
            elif i == 3:
                while True:
                    print('Rejoin a game')
                    print('(Blank) Refresh')
                    print('''(    0) Don't Rejoin a Game''')
                    for id, table in sorted(tables.items()):
                        if not table['running']:
                            continue
                        if table['running'] and not table['joined']:
                            continue
                        print('({:>5}) {}, Players: {}/{}, Variant: {}'.format(
                            id, table['name'], table['num_players'],
                            table['max_players'],
                            Variant(table['variant']).full_name))
                    try:
                        t = int(input('--> '))
                    except ValueError:
                        conn.wait(seconds=waitTime)
                        continue
                    if t == 0:
                        break
                    conn.wait(seconds=waitTime)
                    if t not in tables:
                        print('Game does not exist')
                        continue
                    if not tables[t]['running']:
                        print('Table has not yet started')
                        continue
                    d = {'type': 'reattend_table', 'resp': {'table_id': t}}
                    conn.emit('message', d)
                    break
                conn.wait(seconds=waitTime)

            conn.wait(seconds=waitTime)
            while game is not None:
                conn.wait(seconds=waitTime)
    finally:
        conn.disconnect()

    print('Ended')


if __name__ == '__main__':
    parser: argparse.ArgumentParser
    parser = argparse.ArgumentParser(description='Run an AI bot on keldon.net')
    parser.add_argument('-b', '--bot', default='bot.ini', help='bot ini')
    parser.add_argument('-l', '--login', default='user.ini',
                        help='user info ini')
    parser.add_argument('-u', '--username', nargs='?', default=True,
                        help='Keldon username')
    parser.add_argument('-p', '--password', nargs='?', default=True,
                        help='Keldon password')
    args: argparse.Namespace = parser.parse_args()
    askUsername: bool = False
    askPassword: bool = False
    username: str
    password: str
    if args.login is not None and os.path.isfile(args.login):
        user: configparser.ConfigParser = configparser.ConfigParser()
        user.read(args.login)
        username = user['USER']['username']
        password = user['USER']['password']
    else:
        askUsername = True
        askPassword = True
    if args.username is None:
        askUsername = True
        askPassword = True
    elif isinstance(args.username, str):
        askUsername = False
        username = args.username
    if args.password is None:
        askPassword = True
    elif isinstance(args.password, str):
        askPassword = False
        password = args.password
    if askUsername:
        username = input('Username: ')
    if askPassword:
        password = getpass.getpass('Password:')
    run(username, password, args.bot)
