from __future__ import absolute_import, division, print_function

import os

from datetime import datetime

import attr

import treq

from twisted.internet.defer import DeferredList, inlineCallbacks, returnValue
from twisted.internet.task import LoopingCall
from twisted.internet.threads import deferToThread
from twisted.logger import Logger

from twython import Twython

# set the observers up in main
log = Logger(namespace=u'gaspocket.bot')

GOOD = u'GOOD'
BAD = u'BAD'

STATUS_IO_GOOD = u'All Systems Operational'
GITHUB_GOOD = u'good'

GITHUB = u'https://status.github.com/api/status.json'
CODECOV = u'https://wdzsn5dlywj9.statuspage.io/api/v2/status.json'
TRAVIS = u'https://pnpcptp8xh9k.statuspage.io/api/v2/status.json'


@attr.s
class Context(object):
    state = attr.ib()
    last_update = attr.ib()


@inlineCallbacks
def http_json(url):
    log.info(u'Calling {url}', url=url)
    response = yield treq.get(url)
    log.info(u'Got json response for {url}', url=url)
    json_response = yield response.json()
    returnValue(json_response)


def parse_statusio(status):
    return status[u'status'][u'description']


def parse_github(status):
    return status[u'status']


@inlineCallbacks
def get_json_status(url):
    parsed_json = yield http_json(url)
    returnValue(parsed_json)


def red_alert(codecov, travis, github):
    if (github == GITHUB_GOOD and
        travis == STATUS_IO_GOOD and
        codecov == STATUS_IO_GOOD):  # NOQA
        return GOOD
    else:
        return BAD


def tweet(message, env=os.environ):
    tweeter = Twython(
        env[b'API_KEY'],
        env[b'API_SECRET'],
        env[b'ACCESS_TOKEN'],
        env[b'ACCESS_TOKEN_SECRET']
    )
    try:
        tweeter.update_status(status=message)
    except Exception as e:  # yea, this should be more precise.
        log.info(u'{exc}', exc=str(e))


def create_tweet_msg(s0, s1):
    msg = None
    if s0 == BAD and s1 == BAD:
        log.info('status={status}', status=u'still bad')

    elif s0 == GOOD and s1 == GOOD:
        log.info(u'status={status}', status=u'still good')

    elif s0 == GOOD and s1 == BAD:
        msg = u'expect problems'
        log.info(u'status={status}', status=msg)

    elif s0 == BAD and s1 == GOOD:
        msg = u'Builds should be back to normal'
        log.info(u'status={status}', status=msg)
    return msg


@inlineCallbacks
def run_world(context):

    travis, codecov, github = yield DeferredList(
        [
            get_json_status(TRAVIS),
            get_json_status(CODECOV),
            get_json_status(GITHUB)
        ]
    )
    parsed_github = parse_github(github[1])
    parsed_travis = parse_statusio(travis[1])
    parsed_codecov = parse_statusio(codecov[1])

    new_state = red_alert(parsed_codecov, parsed_travis, parsed_github)

    log.info(u'updated_at={s0_update}, s0={s0_state}, s1={s1}',
             s0_update=context.last_update,
             s0_state=context.state,
             s1=new_state)

    msg = create_tweet_msg(context.state, new_state)
    if msg is not None:
        yield deferToThread(tweet, message=msg)

    context.state = new_state
    context.last_update = datetime.now()

    returnValue(context)


def run(reactor):
    context = Context(state=GOOD, last_update=datetime.now())
    period_seconds = 2 * 60
    l = LoopingCall(run_world, context)
    return l.start(period_seconds)
