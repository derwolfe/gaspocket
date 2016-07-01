"""Twitter bot that tweets a random line from a file.

Uses Twisted to periodically select a random line from an input file,
and Twython to post it to Twitter using your credentials.

Usage: python twitterbot.py file.txt, where each line in file.txt is
a single sentence terminated by a newline ('\n').
"""

import sys
import datetime

import treq

from twisted.internet import task, reactor
from twisted.internet.defer import inlineCallbacks

from twython import Twython

TIMEOUT = datetime.timedelta(hours=1).seconds
twitter = Twython("YOUR API KEY",
                  "YOUR API SECRET",
                  "YOUR ACCESS TOKEN",
                  "YOUR ACCESS TOKEN SECRET")


def parse_travis(feed):
    pass


def parse_codecov(fixed):
    pass


def get_github_status():
    # https://status.github.com/api/status.json
    # returns:
    # {
    #    "status": "good",
    #    "last_updated": "2012-12-07T18:11:55Z"
    # }
    pass


@inlineCallbacks
def get_codecov_status():
    # http://status.codecov.io/history.atom
    pass


def get_travis_status():
    # https://www.traviscistatus.com/history.atom
    pass



# def tweet(check):
#     """Tweet sentence to Twitter."""
#     try:
#         sys.stdout.write("{} {}\n".format(len(sentence), sentence))
#         twitter.update_status(status=sentence)
#     except:
#         pass


# def do_tweet(file_name):
#     """Get line and tweet it"""
#     line = get_line(file_name)
#     tweet(line)


# if __name__ == '__main__':
#     file_name = str(sys.argv[1])
#     l = task.LoopingCall(do_tweet, file_name)
#     l.start(TIMEOUT)
#     # just use react
#     reactor.run()
