import tornado.gen
import logging

from dump import Dump
from playbook import Playbook

log = logging.getLogger(__name__)

class Reactor(object):
    def __init__(self, tok, channel, dump_path, opts):
        self.tok = tok
        self.channel = channel
        self.minion_id = opts['id']
        self.machine_id = opts['machine_id']
        self.master = opts['master']

        dump = Dump(dump_path)
        self.playbook = Playbook(dump, {
            'tok': self.tok,
            'id': self.minion_id,
            'machine_id': self.machine_id,
            'master': self.master,
            'master_ip': self.master,
        })

    @tornado.gen.coroutine
    def start(self):
        self.dispatch({'load': {'fun': None, 'arg': None, 'tgt': self.minion_id, 'load': None, 'jid': None}})

    @tornado.gen.coroutine
    def dispatch(self, load):
        load = load['load']
        fun = load['fun']
        tgt = load['tgt']

        if tgt != '*' and self.minion_id not in tgt:
            log.debug("Ignoring %s call that targets %s, not me (%s)", fun, tgt, self.minion_id)
            return

        reactions = self.playbook.reactions_to(load)
        if reactions:
            ret = yield self.react(load, reactions)
        else:
            log.error("Could not find dispatcher for %s", fun)

    @tornado.gen.coroutine
    def react(self, load, reactions):
        for reaction in reactions:
            request = reaction['load']
            if request['cmd'] == '_return' and request.get('fun') == load.get('fun'):
                request['jid'] = load['jid']
                if load.has_key('metadata'):
                    request['metadata']['suma-action-id'] = load['metadata'].get('suma-action-id')
            yield self.channel.send(request, timeout=60)
