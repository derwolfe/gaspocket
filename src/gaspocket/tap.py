from __future__ import absolute_import, division, print_function

from datetime import datetime


from gaspocket.bot import (
    Context,
    GOOD,
    HTTPApi,
    run_world
)

from twisted.application import internet, service
from twisted.python import usage
from twisted.web.server import Site


class Options(usage.Options):
    optParameters = [['host', 'h', '0.0.0.0',
                      'IP address of interface to listen'],
                     ['port', 'p', '8080', 'Port to listen on']]


def makeService(options):  # NOQA
    context = Context(
        state=GOOD,
        messages={},
        last_update=datetime.now().isoformat()
    )

    # the website
    port = int(options['port'])
    interface = options['host']

    api = HTTPApi(context=context)
    site = Site(api.app.resource)
    http = internet.TCPServer(
        port,
        site,
        interface=interface
    )

    # the updater service
    period_seconds = 2 * 60
    updater = internet.TimerService(
        period_seconds,
        run_world,
        context
    )

    # make a multiservice to link them together
    s = service.MultiService()
    updater.setServiceParent(s)
    http.setServiceParent(s)

    return s
