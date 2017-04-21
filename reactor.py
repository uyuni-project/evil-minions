import tornado.gen
import logging

log = logging.getLogger(__name__)

class Reactor(object):
    def __init__(self, minion_id, channel):
        self.minion_id = minion_id
        self.channel = channel

    @tornado.gen.coroutine
    def ret(self, load, ret):
        ret.update({
            'fun_args': load['arg'],
            'jid': load['jid'],
            'cmd': '_return',
            'fun': load['fun'],
            'id': self.minion_id
        })
        yield self.channel.send(ret, timeout=60)

    @tornado.gen.coroutine
    def dispatch(self, load):
        load = load['load']
        fun = load['fun']
        tgt = load['tgt']

        if tgt != '*' and self.minion_id not in tgt:
            log.debug("Ignoring %s call that targets %s, not me (%s)", fun, tgt, self.minion_id)
            return

        try:
            dispatcher = getattr(self, fun.replace(".", "_"))
            yield self.ret(load, dispatcher(load))
        except AttributeError:
            log.error("Could not find dispatcher for %s", fun)

    def test_ping(self, load):
        return {
            'return': True,
            'retcode': 0,
            'success': True,
        }

    def saltutil_find_job(self, load):
        return {
            'return': {},
            'retcode': 0,
            'success': True,
        }
