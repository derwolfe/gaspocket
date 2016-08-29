"""
Application plugin for twistd
"""

from twisted.application.service import ServiceMaker

gaspocket = ServiceMaker(
    'gaspocket',
    'gaspocket.tap',
    'Run the gaspocket site and updater',
    'gaspocket'
)
