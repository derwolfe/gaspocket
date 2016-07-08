from __future__ import absolute_import, division, print_function

import os
import re

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


REGEX = re.compile(r'\b(fixed|good|resolved)\b', re.IGNORECASE)


@attr.s
class Context(object):
    # state is a boolean, if true then stormy
    alert_state = attr.ib()
    last_update = attr.ib()


@inlineCallbacks
def http_json(url):
    log.info("Calling {url}", url=url)
    response = yield treq.get(url)
    log.info("Got json response for {url}", url=url)
    json_response = yield response.json()
    returnValue(json_response)


@inlineCallbacks
def http_content(url):
    log.info("Calling {url}", url=url)
    response = yield treq.get(url)
    log.info("Got content response for {url}", url=url)
    content = yield treq.content(response)
    returnValue(content)


def parse_atom_feed(feed, threshold_time):
    log.debug("{status}", status="parsing")
    data = feedparser.parse(feed)
    entries = [e for e in data["items"]]

    filtered = []
    for entry in entries:
        entry_time_struct = entry['updated_parsed']
        entry_time = datetime.fromtimestamp(mktime(entry_time_struct))

        if entry_time > threshold_time:
            filtered.append(entry)

    log.debug("{status}", status="done parsing")
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
    # return true if an alert should fire.
    return github == u'bad' or len(travis) > 0 or len(codecov) > 0


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
    except Exception as e:  # yea, this should be more precise.
        log.info("{exc}", exc=str(e))


def fixed(entries):
    for entry in entries:
        entry_html = entry['content'][0]['value']
        match = REGEX.search(entry_html)
        if match is not None:
            return True
        else:
            continue
    return False


@inlineCallbacks
def check_status(context, period):
    threshold = datetime.now() - timedelta(seconds=period)

    travis, codecov, github = yield DeferredList(
        [
            get_travis_status(threshold),
            get_codecov_status(threshold),
            get_github_status()
        ]
    )
    new_state = red_alert(codecov[1], travis[1], github[1])

    codecov_fixed = fixed(codecov[1])
    travis_fixed = fixed(travis[1])
    repaired = bool(codecov_fixed or travis_fixed)

    log.info('updated_at={s0_update},s0={s0_alert_state}, s1={s1}',
             s0_update=context.last_update,
             s0_alert_state=context.alert_state,
             s1=new_state)

    # both are in error state
    if new_state and context.alert_state:
        log.info('status={status}', status='still bad')

    # both are in happy state
    elif not new_state and not context.alert_state:
        log.info('status={status}', status='still good')

    # happy state to error state
    elif new_state and not context.alert_state:
        msg = 'expect problems'
        log.info('status={status}', status=msg)
        yield deferToThread(tweet, message=msg)

    # error state to happy state
    elif repaired and context.alert_state:
        msg = 'Builds should be back to normal'
        log.info('status={status}', status=msg)
        yield deferToThread(tweet, message=msg)

    # update state
    if repaired:
        context.alert_state = False
    else:
        context.alert_state = new_state
    context.last_update = datetime.now()

    returnValue(context)


def run(reactor):
    context = Context(alert_state=False, last_update=datetime.now())
    period_seconds = 5 * 60
    l = LoopingCall(check_status, context, period_seconds)
    return l.start(period_seconds)
