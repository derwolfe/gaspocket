from __future__ import absolute_import, division, print_function

from twisted.internet.task import react

from effect import (
    ComposedDispatcher,
    TypeDispatcher
)

from txeffect import make_twisted_dispatcher, perform

from gaspocket import bot


def get_dispatcher(reactor):
    return ComposedDispatcher([
        TypeDispatcher({
            bot.HTTPContentRequest: bot.perform_content_request_with_treq,
            bot.HTTPJSONRequest: bot.perform_json_request_with_treq,
        }),
        make_twisted_dispatcher(reactor),
    ])


def main(reactor):
    dispatcher = get_dispatcher(reactor)
    # how to get this to see something that does itself produce an effect?
    return perform(dispatcher, bot.run)

if __name__ == '__main__':
    react(main, [])
