from __future__ import absolute_import, division, print_function

import os

from datetime import datetime, timedelta

from time import mktime

import attr

import feedparser

import treq

from twisted.internet.defer import DeferredList, inlineCallbacks, returnValue
from twisted.internet.task import LoopingCall
from twisted.internet.threads import deferToThread
from twisted.logger import Logger

from twython import Twython

# set the observers up in main
log = Logger(namespace="gaspocket.bot")


@attr.s
class Context(object):
    # state is a boolean, if true then stormy
    alert_state = attr.ib()
    last_update = attr.ib()


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
    # return true if unhappy false if happy
    return github != u'good' or codecov or travis


def tweet(message, env=os.environ):
    twitter = Twython(
        env['API_KEY'],
        env['API_SECRET'],
        env['ACCESS_TOKEN'],
        env['ACCESS_TOKEN_SECRET']
    )
    # try except?
    try:
        twitter.update_status(status=message)
    except Exception:  # yea, this should be more precise.
        pass


@inlineCallbacks
def check_status(context):
    threshold = datetime.now() - timedelta(hours=2)

    travis, codecov, github = yield DeferredList(
        [
            get_travis_status(threshold),
            get_codecov_status(threshold),
            get_github_status()
        ]
    )

    new_state = red_alert(codecov[1], travis[1], github[1])

    # new_state = false, current_state = false -> do nothing
    # new_state = true, current_state = true -> do nothing
    # new_state = false, current_state = true -> alert
    # new_state = true, current_state = true -> alert

    log.info('{0}, {1}'.format(new_state, context.alert_state))

    # both are in error state
    if new_state and context.alert_state:
        log.info('still bad')

    # both are in happy state
    elif not new_state and not context.alert_state:
        log.info('still good')

    # happy state to error state
    elif new_state and not context.alert_state:
        msg = 'expect problems'
        yield deferToThread(tweet, message=msg)

    # error state to happy state
    elif not new_state and context.alert_state:
        msg = 'Builds should be back to normal'
        yield deferToThread(tweet, message=msg)

    context.state = new_state
    context.last_update = datetime.now()

    # return the new state of the world
    returnValue(context)


def run(reactor):
    context = Context(alert_state=False, last_update=datetime.now())
    l = LoopingCall(check_status, context)
    minutes = 5 * 60  # every five minutes
    return l.start(minutes)
