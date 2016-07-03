from __future__ import absolute_import, division, print_function

from datetime import datetime

import json

from effect.testing import resolve_effect

# treated like a 3rd party package since in path
from gaspocket.bot import (
    get_codecov_status,
    get_github_status,
    get_travis_status,
    parse_atom_feed,
    red_alert
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
    def test_get_codecov_status_request_success(self):
        with open(self.codecov_atom, 'r') as f:
            status_page = f.read()
        threshold_time = datetime(2016, 6, 30, 10, 0)
        # mock
        stati = yield get_codecov_status(threshold_time)
        self.assertEqual(1, len(resolve_effect(eff, status_page)))

    @inlineCallbacks
    def test_get_travis_status_request_success(self):
        with open(self.travis_atom, 'r') as f:
            status_page = f.read()


        threshold_time = datetime(2016, 6, 30, 10, 0)
        stati = yield get_codecov_status(threshold_time)
        self.assertEqual(2, len(result))

    @inlineCallbacks
    def test_get_github_status_request_success(self):
        response = u'''
{
  "status": "good",
  "last_updated": "2012-12-07T18:11:55Z"
}
'''
        status = yield get_github_status()
        self.assertEqual(
            u'good',
            status
        )


class RedAlertTests(SynchronousTestCase):

    def test_no_alert_conditions(self):
        c, t, g = ([], [], u'good')
        self.assertFalse(red_alert(c, t, g))

    def test_alert_conditions(self):
        c, t, g = ([], [1], u'good')
        self.assertTrue(red_alert(c, t, g))

        c, t, g = ([1], [], u'good')
        self.assertTrue(red_alert(c, t, g))

        c, t, g = ([], [], u'bad')
        self.assertTrue(red_alert(c, t, g))

        c, t, g = ([], [1], u'bad')
        self.assertTrue(red_alert(c, t, g))

        c, t, g = ([1], [1], u'bad')
        self.assertTrue(red_alert(c, t, g))
