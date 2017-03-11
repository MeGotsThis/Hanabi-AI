import argparse
import configparser
import hashlib
import importlib
import os.path
import sys
import threading
import time

from collections import ChainMap
from typing import Mapping, List, Optional, Tuple, Type, Union

import socketIO_client
import six

from bot.bot import Bot
from game import Game
from enums import Variant

_errorObj: object = object()

six.b = lambda s: s.encode()

waitTime: float = 0.1
terminate: bool = False
startGame: bool = True
currentTableId: Optional[int] = None


class MasterBot(threading.Thread):
    def __init__(self,
                 username: str,
                 password: str,
                 botModule: str,
                 botconfig: Mapping,
                 numPlayers: int,
                 variant: Variant,
                 spectators: bool,
                 gameName: str,
                 *args,
                 **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.username: str = username
        self.password: str = password
        module = importlib.import_module(botModule + '.bot')
        self.botCls: Type[Bot] = module.Bot  # type: ignore
        self.botconfig: Mapping = botconfig
        self.numPlayers: int = numPlayers
        self.variant: Variant = variant
        self.spectators: bool = spectators
        self.gameName: str = gameName
        self.conn: socketIO_client.SocketIO
        self.tablePlayers: List[str] = []
        self.readyToStart: bool = False
        self.game: Optional[Game] = None

    def on_message(self, *args):
        global currentTableId
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
            pass
        elif mtype == 'table_gone':
            pass
        elif mtype == 'joined':
            currentTableId = data['table_id']
        elif mtype == 'left':
            print(self.username + ': Game Terminated')
            self.game = None
        elif mtype == 'table_ready':
            self.readyToStart = data['ready']
        elif mtype == 'game':
            self.tablePlayers.clear()
        elif mtype == 'game_player':
            self.tablePlayers.append(data['name'])
        elif mtype == 'game_start':
            while not startGame:
                time.sleep(.1)
            print(self.username + ': Game Started')
            self.conn.emit('message', {'type': 'hello', 'resp': {}})
        elif mtype == 'init':
            self.game = Game(self.conn, Variant(data['variant']),
                             data['names'], data['seat'], self.botCls,
                             **self.botconfig)
            print(self.username + ': Game Loaded')
            self.conn.emit('message', {'type': 'ready', 'resp': {}})
        elif mtype in ['hello', 'user', 'user_left', 'chat',
                       'game_history', 'history_detail', 'game_error',
                       'connected']:
            pass
        elif self.game is not None:
            self.game.received(mtype, data)
            if mtype == 'notify' and data['type'] == 'game_over':
                self.game = None
        elif mtype == 'notify' and data['type'] == 'reveal':
            pass
        elif mtype == 'action':
            pass
        else:
            print(mtype, data)
            raise Exception()

    def run(self) -> None:
        print(self.username + ': Loading Bot AI')
        print(self.username + ': Loaded ' + self.botCls.BOT_NAME)  # type: ignore

        self.conn = socketIO_client.SocketIO('keldon.net', 32221)
        self.conn.on('message', self.on_message)

        print(self.username + ': Connected to keldon.net')


        passBytes = b'Hanabi password ' + self.password.encode()
        passSha: str
        passSha = hashlib.sha256(passBytes).hexdigest()

        d: dict
        try:
            login: dict = {'username': self.username, 'password': passSha}
            self.conn.emit('message', {'type': 'login', 'resp': login})
            self.conn.wait(seconds=1)

            try:
                d = {'type': 'create_table',
                     'resp': {'name': gameName,
                              'max': self.numPlayers,
                              'variant': self.variant.value,
                              'allow_spec': spectators}}
                self.conn.emit('message', d)
                self.conn.wait(seconds=1)
                assert currentTableId is not None
                while (not terminate and not self.readyToStart
                       and len(self.tablePlayers) != self.numPlayers):
                    self.conn.wait(seconds=1)
            except:
                self.conn.emit('message', {'type': 'leave_table', 'resp': {}})
                return

            self.conn.emit('message', {'type': 'start_game', 'resp': {}})

            while self.game is None:
                self.conn.wait(seconds=waitTime)
            while self.game is not None:
                self.conn.wait(seconds=waitTime)

        finally:
            self.conn.disconnect()
            print(self.username + ': Ended')


class SlaveBot(threading.Thread):
    def __init__(self,
                 username: str,
                 password: str,
                 botModule: str,
                 botconfig: Mapping,
                 *args,
                 **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.username: str = username
        self.password: str = password
        module = importlib.import_module(botModule + '.bot')
        self.botCls: Type[Bot] = module.Bot  # type: ignore
        self.botconfig: Mapping = botconfig
        self.conn: socketIO_client.SocketIO
        self.game: Optional[Game] = None

    def on_message(self, *args):
        global currentTableId
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
            pass
        elif mtype == 'table_gone':
            pass
        elif mtype == 'joined':
            pass
        elif mtype == 'left':
            print(self.username + ': Game Terminated')
            pass
            self.game = None
        elif mtype == 'table_ready':
            pass
        elif mtype == 'game':
            pass
        elif mtype == 'game_player':
            pass
        elif mtype == 'game_start':
            while not startGame:
                time.sleep(.1)
            print(self.username + ': Game Started')
            self.conn.emit('message', {'type': 'hello', 'resp': {}})
        elif mtype == 'init':
            self.game = Game(self.conn, Variant(data['variant']),
                             data['names'], data['seat'], self.botCls,
                             **self.botconfig)
            print(self.username + ': Game Loaded')
            self.conn.emit('message', {'type': 'ready', 'resp': {}})
        elif mtype in ['hello', 'user', 'user_left', 'chat',
                       'game_history', 'history_detail', 'game_error',
                       'connected']:
            pass
        elif self.game is not None:
            self.game.received(mtype, data)
            if mtype == 'notify' and data['type'] == 'game_over':
                self.game = None
        elif mtype == 'notify' and data['type'] == 'reveal':
            pass
        elif mtype == 'action':
            pass
        else:
            print(mtype, data)
            raise Exception()

    def run(self) -> None:
        print(self.username + ': Loading Bot AI')
        print(self.username + ': Loaded ' + self.botCls.BOT_NAME)  # type: ignore

        self.conn = socketIO_client.SocketIO('keldon.net', 32221)
        self.conn.on('message', self.on_message)

        print(self.username + ': Connected to keldon.net')


        passBytes = b'Hanabi password ' + self.password.encode()
        passSha: str
        passSha = hashlib.sha256(passBytes).hexdigest()

        try:
            login: dict = {'username': self.username, 'password': passSha}
            self.conn.emit('message', {'type': 'login', 'resp': login})
            while currentTableId is None:
                self.conn.wait(seconds=1)

            d = {'type': 'join_table',
                 'resp': {'table_id': currentTableId}}
            self.conn.emit('message', d)
            self.conn.wait(seconds=1)
            assert currentTableId is not None
            self.conn.wait(seconds=1)

            while self.game is None:
                self.conn.wait(seconds=waitTime)
            while self.game is not None:
                self.conn.wait(seconds=waitTime)

        finally:
            self.conn.disconnect()
            print(self.username + ': Ended')



if __name__ == '__main__':
    parser: argparse.ArgumentParser
    parser = argparse.ArgumentParser(
        description='Run multiple AI bots on keldon.net')
    parser.add_argument('-c', '--config', default='multiple.ini',
                        help='config ini')
    args: argparse.Namespace = parser.parse_args()
    config: configparser.ConfigParser = configparser.ConfigParser()
    config.read(args.config)

    numBots: int = int(config['MULTIPLE']['bots'])
    numHuman: int = int(config['MULTIPLE']['human'])
    totalPlayers = numBots + numHuman
    if numBots < 1:
        raise ValueError('No bots?')
    if totalPlayers < 2 or totalPlayers > 5:
        raise ValueError('Too many/too little players')
    variant: Variant = Variant(int(config['MULTIPLE']['variant']))
    spectators: bool = bool(config['MULTIPLE']['spectator'])
    gameName: str = config['MULTIPLE']['game-name']
    logins: List[Tuple[str, str]] = []
    botModule: List[str] = []
    botConfig: List[ChainMap] = []
    for i in range(numBots):
        username: str
        password: str
        if ('login' in config['LOGIN.' + str(i)]
                and os.path.isfile(config['LOGIN.' + str(i)]['login'])):
            login: configparser.ConfigParser = configparser.ConfigParser()
            login.read(config['LOGIN.' + str(i)]['login'])
            username = login['USER']['username']
            password = login['USER']['password']
        else:
            username = config['LOGIN.' + str(i)]['username']
            password = config['LOGIN.' + str(i)]['password']
        logins.append((username, password))
        bModule: str = config['BOT']['bot']
        if ('BOT.' + str(i)) in config:
            bModule = config['BOT.' + str(i)]['bot']
        botModule.append(bModule)
        bConfig: ChainMap = ChainMap(config['BOT'])
        if ('BOT.' + str(i)) in config:
            bConfig.new_child(config['BOT.' + str(i)])
        if bModule in config:
            bConfig.new_child(config[bModule])
        if (bModule + '.' + str(i)) in config:
            bConfig.new_child(config[bModule + '.' + str(i)])
        botConfig.append(bConfig)
    startGame = not config['MULTIPLE']['prompt-start']

    print('Starting Multi-Bot AI')

    threads: List[Union[MasterBot, SlaveBot]] = []
    threads.append(MasterBot(logins[0][0], logins[0][1], botModule[0],
                             botConfig[0], totalPlayers, variant, spectators,
                             gameName))
    for i in range(1, numBots):
        threads.append(SlaveBot(logins[i][0], logins[i][1], botModule[i],
                                botConfig[i]))
    for thread in threads:
        thread.start()
    try:
        while all(map(threading.Thread.is_alive, threads)):
            time.sleep(.1)
            if currentTableId is not None and not startGame:
                input('Press Enter to continue...')
                startGame = True
    except (KeyboardInterrupt, SystemExit):
        terminate = True
