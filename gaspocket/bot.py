from __future__ import absolute_import, division, print_function

from datetime import datetime
from time import mktime

from effect import Effect

import feedparser

import treq

from twisted.internet.defer import inlineCallbacks, returnValue

from txeffect import deferred_performer

# from twisted.internet import reactor, task


# from twython import Twython

# TIMEOUT = datetime.timedelta(hours=1).seconds
# twitter = Twython("YOUR API KEY",
#                   "YOUR API SECRET",
#                   "YOUR ACCESS TOKEN",
#                   "YOUR ACCESS TOKEN SECRET")


@deferred_performer
def perform_content_request_with_treq(dispatcher, http_request):
    return treq.get(http_request.url).addCallback(treq.content)


@deferred_performer
def perform_json_request_with_treq(dispatcher, http_request):
    return treq.get(http_request.url).addCallback(treq.json)


class HTTPContentRequest(object):

    def __init__(self, url):
        self.url = url

    def __repr__(self):
        return "HTTPContentRequest(%r)" % (self.url,)


class HTTPJSONRequest(object):

    def __init__(self, url):
        self.url = url

    def __repr__(self):
        return "HTTPJSONRequest(%r)" % (self.url,)


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
    response = yield Effect(
        HTTPJSONRequest(b'https://status.github.com/api/status.json')
    )
    returnValue(response.on(success=lambda r: r[u'status']))


@inlineCallbacks
def _get_statuspage_io_status(target, threshold_time):
    response = yield Effect(
        HTTPContentRequest(target)
    )
    returnValue(
        response.on(
            success=lambda feed: parse_atom_feed(feed, threshold_time)
        )
    )


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
    """
    If any of these are producing error messages, then we should alert.

    :param codecov: a list of new codecov statuses from the period
        of time we care about.
    :param travis: a list of new travis statuses from the period
        of time we care about.
    :param github: a string with github's status, either good or bad.

    :returns: True or False
    """
    return github != u'good' or codecov or travis


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
