from __future__ import absolute_import, division, print_function

from datetime import datetime

from twisted.python.filepath import FilePath
from twisted.trial.unittest import SynchronousTestCase

from ..gaspocket.bot import get_codecov_status, parse_atom_feed


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


class TestFetchCodecovStatus(SynchronousTestCase):

    def test_fetches_feed(self):
        d = get_codecov_status()

        def check(result):
            print(result)
            self.assertTrue(True)
        d.addCallback(check)
        return d

    # def test_parse_atom_feed(self):
    # make a feed file and check that it parses
