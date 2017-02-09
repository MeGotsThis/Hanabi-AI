import configparser
import importlib
import time

from collections import ChainMap
from datetime import datetime
from multiprocessing import Pool

from server import ServerGame
from enums import Rank, Variant


def run(args):
    variant, players, bot, kwargs = args
    game = ServerGame(variant, players, bot, **kwargs)
    game.run_game()
    return game


def simulate(config, mapFunc):
    bot = importlib.import_module(config['BOT']['bot'] + '.bot').Bot

    kwargs = config['BOT']
    if config['BOT']['bot'] in config:
        kwargs = ChainMap(config[config['BOT']['bot']],
                          config['BOT'])

    runs = int(config['SIMULATOR']['runs'])
    if runs < 0:
        print('Invalid number of runs')
        return

    variant = Variant(int(config['SIMULATOR']['variant']))
    players = int(config['SIMULATOR']['players'])
    if players < 2 or players > 5:
        print('Invalid number of players')
        return

    print('Starting Game Simulator')
    print('Bot: {}'.format(bot.BOT_NAME))
    print('Variant: {}'.format(variant.full_name))
    print('Players: {}'.format(players))
    print('Started: {}'.format(datetime.now()))
    print()

    start = time.time()
    args = variant, players, bot, kwargs
    allArgs = (args for _ in range(runs))

    maxScore = len(variant.pile_suits) * len(Rank)
    doneScores = {s: 0 for s in range(maxScore + 1)}
    lossScores = {s: 0 for s in range(maxScore + 1)}

    check = min(100, runs // 100)
    completed = 0
    for game in mapFunc:
        completed += 1
        scores = doneScores if not game.loss else lossScores
        scores[game.score] += 1
        if completed % check == 0:
            print('{}/{} completed, Current Time: {}'.format(
                completed, runs, datetime.now()))
    if completed % check != 0:
        print('{}/{} completed, Current Time: {}'.format(
            completed, runs, datetime.now()))
    duration = time.time() - start

    print()
    print('Bot: {}'.format(bot.BOT_NAME))
    print('Variant: {}'.format(variant.full_name))
    print('Players: {}'.format(players))
    print()
    print('Number of Games: {}'.format(completed))
    print('Number of Best Score: {}'.format(doneScores[maxScore]))
    print('Number of Losses: {}'.format(sum(lossScores.values())))
    average = (sum(s * c for s, c in doneScores.items())
               + sum(s * c for s, c in lossScores.items())) / completed
    print('Average Score (all): {:.5f}'.format(average))
    count = sum(doneScores.values())
    average = (sum(s * c for s, c in doneScores.items())
               / sum(doneScores.values())) if count != 0 else 0
    print('Average Score (non-loss): {:.5f}'.format(average))
    count = sum(lossScores.values())
    average = (sum(s * c for s, c in lossScores.items())
               / sum(lossScores.values())) if count != 0 else 0
    print('Average Score (loss): {:.5f}'.format(average))
    print()
    print('Non-loss Score Distribution')
    for score in range(maxScore, -1, -1):
        print('Score {}: {}'.format(score, doneScores[score]))
    print()
    print('Loss Score Distribution')
    for score in range(maxScore + 1):
        print('Score {}: {}'.format(score, lossScores[score]))
    print()
    print('Time to Complete: {:.6f}'.format(duration))


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('simulator.ini')

    cores = None
    if config['SIMULATOR']['cores']:
        cores = int(config['SIMULATOR']['cores']) or None

    if cores > 1:
        with Pool(processes=cores) as pool:
            simulate(config, pool.imap_unordered)
    else:
        simulate(config, map)

