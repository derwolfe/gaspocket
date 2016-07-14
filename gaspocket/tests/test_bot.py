from __future__ import absolute_import, division, print_function

import json

import gaspocket

from gaspocket.bot import (
    BAD,
    GITHUB,
    GITHUB_GOOD,
    GOOD,
    STATUS_IO_GOOD,
    TRAVIS,
    get_json_status,
    parse_github,
    parse_statusio,
    red_alert
)

from twisted.internet.defer import inlineCallbacks, succeed
from twisted.trial.unittest import SynchronousTestCase


class TestFetchStatuses(SynchronousTestCase):

    def setupJsonMock(self, response):
        def fake_json(_arg):
            return succeed(json.loads(response))

        self.patch(gaspocket.bot, 'http_json', fake_json)

    @inlineCallbacks
    def test_get_github_status_request_success(self):
        response = u'''
{
  "status": "good",
  "last_updated": "2012-12-07T18:11:55Z"
}
'''
        self.setupJsonMock(response)
        msg = yield get_json_status(GITHUB)
        self.assertEqual(json.loads(response), msg)

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
        msg = yield get_json_status(TRAVIS)
        self.assertEqual(json.loads(response), msg)


class ParseStatusTests(SynchronousTestCase):

    def test_parses_github(self):
        message = {
            u'status': u'good',
            u'last_updated': u'2012-12-07T18:11:55Z'
        }
        self.assertEqual(
            u'good', parse_github(message)
        )

    def test_parses_statusio(self):
        message = {
            u'status': {
                u'description': u'hi'
            }
        }
        self.assertEqual(
            u'hi', parse_statusio(message)
        )


class RedAlertTests(SynchronousTestCase):

    def test_no_alert_conditions(self):
        c, t, g = (STATUS_IO_GOOD, STATUS_IO_GOOD, GITHUB_GOOD)
        self.assertEqual(GOOD, red_alert(c, t, g))

    def test_alert_conditions(self):
        c, t, g = (STATUS_IO_GOOD, u'badness', GITHUB_GOOD)
        self.assertEqual(BAD, red_alert(c, t, g))

        c, t, g = (u'badness', STATUS_IO_GOOD, GITHUB_GOOD)
        self.assertEqual(BAD, red_alert(c, t, g))

        c, t, g = (STATUS_IO_GOOD, STATUS_IO_GOOD, u'bad')
        self.assertEqual(BAD, red_alert(c, t, g))

        c, t, g = (STATUS_IO_GOOD, u'badness',  u'bad')
        self.assertEqual(BAD, red_alert(c, t, g))

        c, t, g = (u'badness', u'badness',  u'bad')
        self.assertEqual(BAD, red_alert(c, t, g))
