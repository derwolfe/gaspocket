from __future__ import absolute_import, division, print_function

from datetime import datetime, timedelta
from time import mktime

import feedparser

import treq

from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.logger import Logger


log = Logger()

# from twython import Twython

# TIMEOUT = datetime.timedelta(hours=1).seconds
# twitter = Twython("YOUR API KEY",
#                   "YOUR API SECRET",
#                   "YOUR ACCESS TOKEN",
#                   "YOUR ACCESS TOKEN SECRET")


@inlineCallbacks
def http_json(url):
    returnValue(treq.get(url).addCallback(lambda r: r.json()))


@inlineCallbacks
def http_content(url):
    returnValue(treq.get(url).addCallback(treq.content))


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
    parsed_json = yield http_json(b'https://status.github.com/api/status.json')
    returnValue(parsed_json[u'status'])


@inlineCallbacks
def _get_statuspage_io_status(target, threshold_time):
    parsed = yield http_content(target)
    returnValue(parse_atom_feed(parsed, threshold_time))


def get_codecov_status(threshold_time):
    return _get_statuspage_io_status(
        target=b'http://status.codecov.io/history.atom',
        threshold_time=threshold_time
    )


def get_travis_status(threshold_time):
    return _get_statuspage_io_status(
        target=b'http://www.traviscistatus.com/history.atom',
        threshold_time=threshold_time
    )


def red_alert(codecov, travis, github):
    return github != u'good' or codecov or travis


@inlineCallbacks
def run():
    # go get some statuses
    threshold = datetime.now() - timedelta(hours=12)
    travis = yield get_travis_status(threshold)
    codecov = yield get_codecov_status(threshold)
    github = yield get_github_status()

    # see if we need to alert
    if red_alert(codecov, travis, github):
        log.info("ALL HELL BREAKING LOOSE")
    else:
        log.info("things are calm")


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
