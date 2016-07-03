from __future__ import absolute_import, division, print_function

from twisted.internet.task import react

from gaspocket.bot import run

from twisted.logger import jsonFileLogObserver, Logger



if __name__ == '__main__':
    react(run, [])
