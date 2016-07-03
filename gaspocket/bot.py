from __future__ import absolute_import, division, print_function

from datetime import datetime, timedelta
from time import mktime

import feedparser

import treq

from twisted.internet.defer import inlineCallbacks, returnValue, DeferredList

from twisted.logger import Logger

# set the observers up in main
log = Logger(namespace="gaspocket.bot")


# from twython import Twython

# TIMEOUT = datetime.timedelta(hours=1).seconds
# twitter = Twython("YOUR API KEY",
#                   "YOUR API SECRET",
#                   "YOUR ACCESS TOKEN",
#                   "YOUR ACCESS TOKEN SECRET")


@inlineCallbacks
def http_json(url):
    log.info("Calling {url}".format(url=url))
    response = yield treq.get(url)
    log.info("Got json response for {url}".format(url=url))
    json_response = yield response.json()
    returnValue(json_response)


@inlineCallbacks
def http_content(url):
    log.info("Calling {url}".format(url=url))
    response = yield treq.get(url)
    log.info("Got content response for {url}".format(url=url))
    content = yield treq.content(response)
    returnValue(content)


def parse_atom_feed(feed, threshold_time):
    log.debug("parsing")
    data = feedparser.parse(feed)
    entries = [e for e in data["items"]]

    filtered = []
    for entry in entries:
        entry_time_struct = entry['updated_parsed']
        entry_time = datetime.fromtimestamp(mktime(entry_time_struct))

        if entry_time > threshold_time:
            filtered.append(entry)
    log.debug("done parsing")
    return filtered


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
def run(reactor):
    threshold = datetime.now() - timedelta(hours=2)

    travis, codecov, github = yield DeferredList(
        [
            get_travis_status(threshold),
            get_codecov_status(threshold),
            get_github_status()
        ]
    )

    error = 0
    if red_alert(codecov[1], travis[1], github[1]):
        log.warn("ALL HELL BREAKING LOOSE")
        error = 1
    else:
        log.info("things are calm")
        error = 0
    returnValue(error)


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
