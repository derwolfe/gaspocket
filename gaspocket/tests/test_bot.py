from __future__ import absolute_import, division, print_function

from datetime import datetime

import json

from effect.testing import resolve_effect

# treated like a 3rd party package since in path
from gaspocket.bot import (
    get_codecov_status,
    get_github_status,
    get_travis_status,
    parse_atom_feed
)

from twisted.internet.defer import inlineCallbacks
from twisted.python.filepath import FilePath
from twisted.trial.unittest import SynchronousTestCase


class AtomParsingTests(SynchronousTestCase):

    def setUp(self):
        atom_fixtures = FilePath(__file__).parent().child('fixtures')
        self.codecov_atom = atom_fixtures.child('codecov.atom').path
        self.travis_atom = atom_fixtures.child('travis.atom').path

    def test_parses_codecov_status_with_events(self):
        """
        Returns codecov events that have happened in the last 12 hours.
        """
        threshold_time = datetime(2016, 6, 30, 10, 0)
        with open(self.codecov_atom, 'r') as f:
            status = f.read()
        result = parse_atom_feed(status, threshold_time)
        self.assertEqual(1, len(result))

    def test_parses_codecov_status_without_events(self):
        """
        Returns no codecov events since none have passed within the last 12
        hours.
        """
        threshold_time = datetime(2016, 7, 30, 0, 0)
        with open(self.codecov_atom, 'r') as f:
            status = f.read()
        result = parse_atom_feed(status, threshold_time)

        self.assertEqual([], result)

    def test_parses_travis_status_with_events(self):
        """
        Returns travis events that have happened in the last 12 hours.
        """
        threshold_time = datetime(2016, 6, 30, 10, 0)
        with open(self.travis_atom, 'r') as f:
            status = f.read()
        result = parse_atom_feed(status, threshold_time)
        self.assertEqual(2, len(result))

    def test_parses_travis_status_without_events(self):
        """
        Returns no travis events since none have passed within the last 12
        hours.
        """
        threshold_time = datetime(2016, 7, 30, 0, 0)
        with open(self.travis_atom, 'r') as f:
            status = f.read()
        result = parse_atom_feed(status, threshold_time)

        self.assertEqual([], result)


class TestFetchStatuses(SynchronousTestCase):

    def setUp(self):
        atom_fixtures = FilePath(__file__).parent().child('fixtures')
        self.codecov_atom = atom_fixtures.child('codecov.atom').path
        self.travis_atom = atom_fixtures.child('travis.atom').path

    @inlineCallbacks
    def test_get_travis_status_request(self):
        eff = yield get_travis_status(datetime.now())
        http = eff.intent
        self.assertEqual(
            b'http://www.traviscistatus.com/history.atom',
            http.url
        )

    @inlineCallbacks
    def test_get_codecov_status_request(self):
        eff = yield get_codecov_status(datetime.now())
        http = eff.intent
        self.assertEqual(
            b'http://status.codecov.io/history.atom',
            http.url
        )

    @inlineCallbacks
    def test_get_github_status_request(self):
        eff = yield get_github_status()
        http = eff.intent
        self.assertEqual(
            b'https://status.github.com/api/status.json',
            http.url
        )

    @inlineCallbacks
    def test_get_codecov_status_request_success(self):
        with open(self.codecov_atom, 'r') as f:
            status_page = f.read()
        threshold_time = datetime(2016, 6, 30, 10, 0)
        eff = yield get_codecov_status(threshold_time)
        self.assertEqual(1, len(resolve_effect(eff, status_page)))

    @inlineCallbacks
    def test_get_travis_status_request_success(self):
        with open(self.travis_atom, 'r') as f:
            status_page = f.read()
        threshold_time = datetime(2016, 6, 30, 10, 0)
        eff = yield get_codecov_status(threshold_time)
        self.assertEqual(2, len(resolve_effect(eff, status_page)))

    @inlineCallbacks
    def test_get_github_status_request_success(self):
        response = u'''
{
  "status": "good",
  "last_updated": "2012-12-07T18:11:55Z"
}
'''
        eff = yield get_github_status()
        self.assertEqual(
            u'good',
            resolve_effect(eff, json.loads(response)))
