from __future__ import absolute_import, division, print_function

import sys

from twisted.internet.task import react

from gaspocket.bot import run

from twisted.logger import jsonFileLogObserver, globalLogPublisher

# use a json logger and push everything to stdout
globalLogPublisher.addObserver(jsonFileLogObserver(sys.stdout))

if __name__ == '__main__':
    react(run, [])
