import configparser
import copy
import importlib
import time

from collections import ChainMap
from datetime import datetime
from math import sqrt
from multiprocessing import Pool
from statistics import mean, median, stdev

from server import ServerGame
from enums import Rank, Variant


def run(args):
    variant, players, bot, kwargs, i = args
    if 'seed' in kwargs and kwargs['seed'] is not None:
        kwargs = copy.copy(kwargs)
        try:
            kwargs['seed'] = int(kwargs['seed']) + i
        except ValueError:
            kwargs['seed'] = kwargs['seed'] + str(i)
    game = ServerGame(variant, players, bot, **kwargs)
    game.run_game()
    return game

def iterateScores(scores):
    for score, count in scores.items():
        for _ in range(count):
            yield score

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
    args = variant, players, bot, dict(kwargs)
    allArgs = (args + (i,) for i in range(runs))

    maxScore = len(variant.pile_suits) * len(Rank)
    doneScores = {s: 0 for s in range(maxScore + 1)}
    lossScores = {s: 0 for s in range(maxScore + 1)}

    check = max(min(100, runs // 100), 1)
    completed = 0
    for game in mapFunc(run, allArgs):
        completed += 1
        scores = doneScores if not game.loss else lossScores
        scores[game.score] += 1
        if game.loss:
            if game.score <= 5:
                for m in game.verbose:
                    print(m)
        if completed % check == 0:
            print('{}/{} completed, Current Time: {}'.format(
                completed, runs, datetime.now()))
    if completed % check != 0:
        print('{}/{} completed, Current Time: {}'.format(
            completed, runs, datetime.now()))
    duration = time.time() - start
    allScores = {s: doneScores[s] + lossScores[s] for s in range(maxScore + 1)}

    scoreDisplay = (('All Games', allScores),
                    ('Non-Loss Games', doneScores),
                    ('Loss Games', lossScores))

    print()
    print('Bot: {}'.format(bot.BOT_NAME))
    print('Variant: {}'.format(variant.full_name))
    print('Players: {}'.format(players))
    print()
    print('Number of Games: {}'.format(completed))
    print('Number of Best Score: {}'.format(doneScores[maxScore]))
    print('Number of Losses: {}'.format(sum(lossScores.values())))
    for scoreType, scores in scoreDisplay:
        print()
        print(scoreType)
        average = 0
        middle = 0
        stdDev = 0
        error = 0
        count = sum(scores.values())
        if count >= 1:
            average = mean(iterateScores(scores))
            middle = median(iterateScores(scores))
        if count >= 2:
            stdDev = stdev(iterateScores(scores))
            error = stdDev / sqrt(count)
        print('Average Score: {:.5f}'.format(average))
        print('Median Score: {:.5f}'.format(middle))
        print('Standard Deviation: {:.5f}'.format(stdDev))
        print('Standard Error: {:.5f}'.format(error))
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

