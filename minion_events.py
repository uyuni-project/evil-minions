import logging
import tornado.gen
import time

log = logging.getLogger(__name__)

@tornado.gen.coroutine
def start(minion_id, tok, channel):
    load = {'id': minion_id,
            'cmd': '_minion_event',
            'pretag': None,
            'tok': tok,
            'tag': "minion_start",
            'data': 'EVIL minion %s started at %s' % (minion_id, time.asctime()) }
    yield channel.send(load, timeout=60)
    load = {'id': minion_id,
            'cmd': '_minion_event',
            'pretag': None,
            'tok': tok,
            'tag': 'salt/minion/%s/start' % minion_id,
            'data': 'EVIL minion %s started at %s' % (minion_id, time.asctime()) }
    yield channel.send(load, timeout=60)
