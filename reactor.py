import tornado.gen
import logging

import raw_data

log = logging.getLogger(__name__)

class Reactor(object):
    def __init__(self, tok, channel, opts):
        self.tok = tok
        self.channel = channel
        self.minion_id = opts['id']
        self.machine_id = opts['machine_id']
        self.master = opts['master']
        self.opts = raw_data.opts(self.minion_id, self.machine_id, self.master)

    @tornado.gen.coroutine
    def ret(self, load, ret):
        result = yield ret
        result.update({
            'cmd': '_return',
            'fun': load['fun'],
            'fun_args': load['arg'],
            'id': self.minion_id,
            'jid': load['jid'],
        })
        yield self.channel.send(result, timeout=60)

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

    @tornado.gen.coroutine
    def test_ping(self, load):
        raise tornado.gen.Return({
            'retcode': 0,
            'return': True,
            'success': True,
        })

    @tornado.gen.coroutine
    def saltutil_find_job(self, load):
        raise tornado.gen.Return({
            'retcode': 0,
            'return': {},
            'success': True,
        })

    @tornado.gen.coroutine
    def saltutil_sync_beacons(self, load):
        yield self.channel.send({ 'cmd': '_master_opts'})
        yield self.channel.send({ 'cmd': '_file_envs'})
        yield self.channel.send({ 'cmd': '_file_envs'})
        yield self.channel.send({ 'cmd': '_file_list', 'prefix': '', 'saltenv': 'base'})
        yield self.channel.send({ 'cmd': '_file_envs'})
        yield self.channel.send({ 'cmd': '_file_envs'})
        yield self.channel.send({ 'cmd': '_file_hash', 'path': u'top.sls', 'saltenv': 'base'})
        yield self.channel.send({ 'cmd': '_ext_nodes', 'id': self.minion_id, 'opts': self.opts, 'tok': self.tok})
        yield self.channel.send({ 'cmd': '_file_list', 'prefix': '', 'saltenv': 'base'})
        yield self.channel.send({ 'cmd': '_file_hash', 'path': u'_grains/pkgset.py', 'saltenv': 'base'})
        yield self.channel.send({ 'cmd': '_file_hash', 'path': u'_grains/virtpoller.py', 'saltenv': 'base'})
        raise tornado.gen.Return({
            'retcode': 0,
            'return': [],
            'success': True
        })

    @tornado.gen.coroutine
    def saltutil_sync_grains(self, load):
        yield self.channel.send({ 'cmd': '_master_opts'})
        yield self.channel.send({ 'cmd': '_file_envs'})
        yield self.channel.send({ 'cmd': '_file_envs'})
        yield self.channel.send({ 'cmd': '_file_list', 'prefix': '', 'saltenv': 'base'})
        yield self.channel.send({ 'cmd': '_file_envs'})
        yield self.channel.send({ 'cmd': '_file_envs'})
        yield self.channel.send({ 'cmd': '_file_hash', 'path': u'top.sls', 'saltenv': 'base'})
        yield self.channel.send({ 'cmd': '_ext_nodes', 'id': self.minion_id, 'opts': self.opts, 'tok': self.tok})
        yield self.channel.send({ 'cmd': '_file_list', 'prefix': '', 'saltenv': 'base'})
        yield self.channel.send({ 'cmd': '_file_hash', 'path': u'_grains/cpuinfo.py', 'saltenv': 'base'})
        raise tornado.gen.Return({
            'retcode': 0,
            'return': [],
            'success': True
        })

    @tornado.gen.coroutine
    def saltutil_sync_modules(self, load):
        yield self.channel.send({ 'cmd': '_master_opts'})
        yield self.channel.send({ 'cmd': '_file_envs'})
        yield self.channel.send({ 'cmd': '_file_envs'})
        yield self.channel.send({ 'cmd': '_file_list', 'prefix': '', 'saltenv': 'base'})
        yield self.channel.send({ 'cmd': '_file_envs'})
        yield self.channel.send({ 'cmd': '_file_envs'})
        yield self.channel.send({ 'cmd': '_file_hash', 'path': u'top.sls', 'saltenv': 'base'})
        yield self.channel.send({ 'cmd': '_ext_nodes', 'id': self.minion_id, 'opts': self.opts, 'tok': self.tok})
        yield self.channel.send({ 'cmd': '_file_list', 'prefix': '', 'saltenv': 'base'})
        yield self.channel.send({ 'cmd': '_file_hash', 'path': u'_modules/mainframesysinfo.py', 'saltenv': 'base'})
        yield self.channel.send({ 'cmd': '_file_hash', 'path': u'_modules/sumautil.py', 'saltenv': 'base'})
        yield self.channel.send({ 'cmd': '_file_hash', 'path': u'_modules/udevdb.py', 'saltenv': 'base'})
        raise tornado.gen.Return({
            'retcode': 0,
            'return': [],
            'success': True
        })

    @tornado.gen.coroutine
    def status_uptime(self, load):
        raise tornado.gen.Return({
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
        })

    @tornado.gen.coroutine
    def grains_items(self, load):
        raise tornado.gen.Return({
            'out': 'nested',
            'retcode': 0,
            'return': {
                self.opts['grains']
            },
            'success': True
        })

    @tornado.gen.coroutine
    def grains_item(self, load):
        if 'machine_id' not in load['arg']:
            log.error("The grains_item dispatcher cannot handle args %s", load['arg'])
        raise tornado.gen.Return({
            'out': 'nested',
            'retcode': 0,
            'return': {
                'machine_id': self.machine_id
            },
            'success': True
        })

    @tornado.gen.coroutine
    def config_get(self, load):
        if load['arg'] != ['master']:
            log.error("The config_get dispatcher cannot handle args %s", load['arg'])
        raise tornado.gen.Return({
            'retcode': 0,
            'return': self.master,
            'success': True
        })

    @tornado.gen.coroutine
    def state_apply(self, load):
        if not any('packages.profileupdate' in arg['mods'] for arg in load['arg']):
            log.error("The config_get dispatcher cannot handle args %s", load['arg'])
        raise tornado.gen.Return({
            'metadata': { 'suma-action-id': load['metadata']['suma-action-id'] },
            'out': 'highstate',
            'retcode': 0,
            'return': raw_data.packages(),
            'success': True
        })
