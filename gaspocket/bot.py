from __future__ import absolute_import, division, print_function

from datetime import datetime
from time import mktime

import feedparser

import treq

# from twisted.internet import reactor, task
from twisted.internet.defer import inlineCallbacks, returnValue


# from twython import Twython

# TIMEOUT = datetime.timedelta(hours=1).seconds
# twitter = Twython("YOUR API KEY",
#                   "YOUR API SECRET",
#                   "YOUR ACCESS TOKEN",
#                   "YOUR ACCESS TOKEN SECRET")


def parse_atom_feed(feed, threshold_time):
    data = feedparser.parse(feed)
    entries = [e for e in data["items"]]
    # only get the most recent
    by_date = sorted(entries, key=lambda entry: entry["date_parsed"])[::-1]

    # return any entries that have taken place between now and the threshold
    # time
    entries = []
    for entry in by_date:
        entry_time_struct = entry['updated_parsed']
        entry_time = datetime.fromtimestamp(mktime(entry_time_struct))

        if entry_time > threshold_time:
            entries.append(entry)

    return entries


@inlineCallbacks
def get_github_status():
    response = yield treq.get(b'https://status.github.com/api/status.json')
    status = yield treq.json(response)

    #
    # returns:
    # {
    #    "status": "good",
    #    "last_updated": "2012-12-07T18:11:55Z"
    # }

    returnValue(status[u'status'])


@inlineCallbacks
def _get_statuspage_io_status(target, threshold_time):
    response = yield treq.get()
    feed = yield treq.content(response)
    data = parse_atom_feed(feed, threshold_time)
    returnValue(data)


@inlineCallbacks
def get_codecov_status(threshold_time):
    data = yield _get_statuspage_io_status(
        target=b'http://status.codecov.io/history.atom',
        threshold_time=threshold_time
    )
    returnValue(data)


@inlineCallbacks
def get_travis_status(threshold_time):
    data = yield _get_statuspage_io_status(
        target=b'http://www.traviscistatus.com/history.atom',
        threshold_time=threshold_time
    )
    returnValue(data)


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
