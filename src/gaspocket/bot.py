from __future__ import absolute_import, division, print_function

import json

import os

from datetime import datetime, timezone

import attr

from klein import Klein

from prometheus_client import Counter
from prometheus_client.twisted import MetricsResource

import treq

from twisted.internet.defer import (
    CancelledError,
    DeferredList,
    inlineCallbacks,
    returnValue
)
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet.task import LoopingCall
from twisted.logger import Logger
from twisted.web.server import Site


# set the observers up in main
log = Logger(namespace=u'gaspocket.bot')

GOOD = u'GOOD'
BAD = u'BAD'

STATUS_IO_GOOD = u'All Systems Operational'
GITHUB_GOOD = u'good'

GITHUB = u'https://status.github.com/api/status.json'
CODECOV = u'https://wdzsn5dlywj9.statuspage.io/api/v2/status.json'
TRAVIS = u'https://pnpcptp8xh9k.statuspage.io/api/v2/status.json'

TIMEOUT_MESSAGE = u'Request timed out'

INBOUND_REQUESTS = Counter(
    u'inbound_requests_total',
    u'HTTP Failures',
    [u'endpoint', u'method']
)
SUCCESSES = Counter(
    u'success_outbound_checks',
    u'Outbound status check successes',
    [u'url']
)
TIMEOUTS = Counter(
    u'timed_out_status_checks',
    u'Outbound status check failures',
    [u'url']
)


@attr.s
class Context(object):
    state = attr.ib()
    last_update = attr.ib()
    messages = attr.ib()


@inlineCallbacks
def _get_json(url):
    log.info(u'Calling {url}', url=url)
    response = yield treq.get(url, timeout=10)
    log.info(u'Got json response for {url}', url=url)
    json_response = yield response.json()
    returnValue(json_response)


def _parse_statusio(status):
    return status[u'status'][u'description']


def _parse_github(status):
    return status[u'status']


@inlineCallbacks
def fetch_and_parse(url):
    try:
        message = yield _get_json(url)
    except CancelledError:
        TIMEOUTS.labels(url).inc()
        log.info(u'Timed out fetching {url}', url=url)
        returnValue(TIMEOUT_MESSAGE)

    SUCCESSES.labels(url).inc()

    if url in [TRAVIS, CODECOV]:
        returnValue(_parse_statusio(message))
    else:
        returnValue(_parse_github(message))


def get_next_state(codecov, travis, github):
    if (github == GITHUB_GOOD and
        travis == STATUS_IO_GOOD and
        codecov == STATUS_IO_GOOD):  # NOQA
        return GOOD
    else:
        return BAD


@inlineCallbacks
def run_world(context):
    travis, codecov, github = yield DeferredList(
        [
            fetch_and_parse(TRAVIS),
            fetch_and_parse(CODECOV),
            fetch_and_parse(GITHUB)
        ]
    )
    # although maybe you could hang off of <foo>[0]
    parsed_github = github[1]
    parsed_travis = travis[1]
    parsed_codecov = codecov[1]

    new_state = get_next_state(parsed_codecov, parsed_travis, parsed_github)

    log.info(
        u'updated_at={context.last_update}, s0={context.state}, s1={s1}',
        context=context,
        s1=new_state
    )

    context.state = new_state
    context.messages = {
        u'github': parsed_github,
        u'travis': parsed_travis,
        u'codecov': parsed_codecov
    }
    context.last_update = datetime.now(timezone.utc).isoformat()
    returnValue(context)


class HTTPApi(object):

    app = Klein()

    def __init__(self, context):
        self.context = context

    @app.route('/')
    def home(self, request):
        INBOUND_REQUESTS.labels(u'/', u'GET').inc()
        request.setHeader(b'Content-Type', b'application/json')
        return json.dumps(attr.asdict(self.context), indent=4)

    @app.route('/metrics')
    def metrics(self, request):
        INBOUND_REQUESTS.labels(u'/metrics', u'GET').inc()
        return MetricsResource()


def run(reactor):
    port = int(os.environ.get(u'PORT', 8080))
    context = Context(
        state=GOOD,
        messages={},
        last_update=datetime.now(timezone.utc).isoformat()
    )

    api = HTTPApi(context=context)
    endpoint = TCP4ServerEndpoint(
        reactor=reactor, port=port, interface=u'0.0.0.0')
    endpoint.listen(Site(api.app.resource()))

    l = LoopingCall(run_world, context)
    period_seconds = 2 * 60
    return l.start(period_seconds)
