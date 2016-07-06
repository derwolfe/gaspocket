from __future__ import absolute_import, division, print_function

import sys

from gaspocket.bot import run

from twisted.internet.task import react

from twisted.logger import globalLogPublisher, jsonFileLogObserver


globalLogPublisher.addObserver(jsonFileLogObserver(sys.stdout))


if __name__ == '__main__':
    react(run, [])
