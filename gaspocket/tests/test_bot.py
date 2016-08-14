from __future__ import absolute_import, division, print_function

import json

from datetime import datetime

import gaspocket

from gaspocket.bot import (
    BAD,
    GITHUB,
    GITHUB_GOOD,
    GOOD,
    STATUS_IO_GOOD,
    TIMEOUT_MESSAGE,
    TRAVIS,
    Context,
    _parse_github,
    _parse_statusio,
    fetch_and_parse,
    get_next_state
)

from twisted.internet.defer import CancelledError, inlineCallbacks, succeed
from twisted.trial.unittest import SynchronousTestCase


class FetchAndParseTests(SynchronousTestCase):

    def setupJsonMock(self, response):
        def fake_json(_arg):
            return succeed(json.loads(response))

        self.patch(gaspocket.bot, '_get_json', fake_json)

    @inlineCallbacks
    def test_get_github_status_request_success(self):
        response = u'''
{
  "status": "good",
  "last_updated": "2012-12-07T18:11:55Z"
}
'''
        self.setupJsonMock(response)
        msg = yield fetch_and_parse(GITHUB)
        self.assertEqual(u'good', msg)

    @inlineCallbacks
    def test_get_statusio_status_request_success(self):
        response = u'''{
    "page": {
        "id": "pnpcptp8xh9k",
        "name": "Travis CI",
        "updated_at": "2016-07-14T16:57:37.489Z",
        "url": "https://www.traviscistatus.com"
    },
    "status": {
        "description": "All Systems Operational",
        "indicator": "none"
    }
}'''
        self.setupJsonMock(response)
        msg = yield fetch_and_parse(TRAVIS)
        self.assertEqual(u'All Systems Operational', msg)

    @inlineCallbacks
    def test_returns_timeout_message_on_timeout(self):
        def timeout(*args, **kwargs):
            raise CancelledError('I timeout')

        self.patch(gaspocket.bot, '_get_json', timeout)

        msg = yield fetch_and_parse(u'who cares')
        self.assertEqual(TIMEOUT_MESSAGE, msg)


class ParseStatusTests(SynchronousTestCase):

    def test_parses_github(self):
        message = {
            u'status': u'good',
            u'last_updated': u'2012-12-07T18:11:55Z'
        }
        self.assertEqual(
            u'good', _parse_github(message)
        )

    def test_parses_statusio(self):
        message = {
            u'status': {
                u'description': u'hi'
            }
        }
        self.assertEqual(
            u'hi', _parse_statusio(message)
        )


class GetNextStateTests(SynchronousTestCase):

    def assertGood(self, result):
        self.assertEqual(GOOD, result)

    def assertBad(self, result):
        self.assertEqual(BAD, result)

    def test_no_alert_conditions(self):
        c, t, g = (STATUS_IO_GOOD, STATUS_IO_GOOD, GITHUB_GOOD)
        self.assertGood(get_next_state(c, t, g))

    def test_alert_conditions(self):
        c, t, g = (STATUS_IO_GOOD, u'badness', GITHUB_GOOD)
        self.assertBad(get_next_state(c, t, g))

        c, t, g = (u'badness', STATUS_IO_GOOD, GITHUB_GOOD)
        self.assertBad(get_next_state(c, t, g))

        c, t, g = (STATUS_IO_GOOD, STATUS_IO_GOOD, u'bad')
        self.assertBad(get_next_state(c, t, g))

        c, t, g = (STATUS_IO_GOOD, u'badness',  u'bad')
        self.assertBad(get_next_state(c, t, g))

        c, t, g = (u'badness', u'badness',  u'bad')
        self.assertBad(get_next_state(c, t, g))


# class GetJsonTests(SynchronousTestCase):

#     def test_returns_parsed_json(self):
#         self.fail()

#     def test_cancels_request_after_timeout_reached(self):
#         self.fail()


# class RunWorldTests(SynchronousTestCase):

#     def _build_context(self):
#         return Context(
#             state=GOOD,
#             messages={},
#             last_update=datetime.now()
#         )

#     def setupTreqMock(self, response):
#         def fake_json(*arg, **kwargs):
#             return succeed(json.loads(response))

#         self.patch(treq, 'get', fake_json)

#     def test_updates_world_on_iteration(self):
#         ctx = self._build_context()
