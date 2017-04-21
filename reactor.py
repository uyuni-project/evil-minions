import tornado.gen
import logging

import opts

log = logging.getLogger(__name__)

class Reactor(object):
    def __init__(self, minion_id, tok, channel):
        self.minion_id = minion_id
        self.tok = tok
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

        dispatcher_name = fun.replace(".", "_")
        try:
            dispatcher = getattr(self, dispatcher_name)
            yield self.ret(load, dispatcher(load))
        except AttributeError:
            log.error("Could not find dispatcher %s", dispatcher_name)

    def test_ping(self, load):
        return {
            'retcode': 0,
            'return': True,
            'success': True,
        }

    def saltutil_find_job(self, load):
        return {
            'retcode': 0,
            'return': {},
            'success': True,
        }

    def saltutil_sync_beacons(self, load):
        yield self.channel.send({ 'cmd': '_master_opts'})
        yield self.channel.send({ 'cmd': '_file_envs'})
        yield self.channel.send({ 'cmd': '_file_envs'})
        yield self.channel.send({ 'cmd': '_file_list', 'prefix': '', 'saltenv': 'base'})
        yield self.channel.send({ 'cmd': '_file_envs'})
        yield self.channel.send({ 'cmd': '_file_envs'})
        yield self.channel.send({ 'cmd': '_file_hash', 'path': u'top.sls', 'saltenv': 'base'})
        yield self.channel.send({ 'cmd': '_ext_nodes', 'id': self.minion_id, 'opts': opts.opts, 'tok': self.tok})
        yield self.channel.send({ 'cmd': '_file_list', 'prefix': '', 'saltenv': 'base'})
        yield self.channel.send({ 'cmd': '_file_hash', 'path': u'_grains/pkgset.py', 'saltenv': 'base'})
        yield self.channel.send({ 'cmd': '_file_hash', 'path': u'_grains/virtpoller.py', 'saltenv': 'base'})
        return {
            'retcode': 0,
            'return': [],
            'success': True
        }

    def saltutil_sync_grains(self, load):
        yield self.channel.send({ 'cmd': '_master_opts'})
        yield self.channel.send({ 'cmd': '_file_envs'})
        yield self.channel.send({ 'cmd': '_file_envs'})
        yield self.channel.send({ 'cmd': '_file_list', 'prefix': '', 'saltenv': 'base'})
        yield self.channel.send({ 'cmd': '_file_envs'})
        yield self.channel.send({ 'cmd': '_file_envs'})
        yield self.channel.send({ 'cmd': '_file_hash', 'path': u'top.sls', 'saltenv': 'base'})
        yield self.channel.send({ 'cmd': '_ext_nodes', 'id': self.minion_id, 'opts': opts.opts, 'tok': self.tok})
        yield self.channel.send({ 'cmd': '_file_list', 'prefix': '', 'saltenv': 'base'})
        yield self.channel.send({ 'cmd': '_file_hash', 'path': u'_grains/cpuinfo.py', 'saltenv': 'base'})
        return {
            'retcode': 0,
            'return': [],
            'success': True
        }

    def status_uptime(self, load):
        return {
            'retcode': 0,
            'return': {
                'days': 0,
                'seconds': 14110,
                'since_iso': '2017-04-21T08:36:20.058937',
                'since_t': 1492756580.0,
                'time': '3:55',
                'users': 2
            },
            'success': True
        }
