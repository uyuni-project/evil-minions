'''Classes to implement responses an EvilMinion returns to its master'''

import logging

import tornado.gen

log = logging.getLogger(__name__)

class Reactor(object):
    '''Reacts to PUB events by responding with REQs from a dump'''
    def __init__(self, tok, channel, dump_reader, opts):
        self.tok = tok
        self.channel = channel
        self.dump_reader = dump_reader

        self.minion_id = opts['id']
        self.machine_id = opts['machine_id']
        self.uuid = opts['uuid']
        self.master = opts['master']

        self.current_time = 0
        self.replacements = dump_reader.get_replacements({
            'tok': self.tok,
            'id': self.minion_id,
            'machine_id': self.machine_id,
            'uuid': self.uuid,
            'master': self.master,
            'master_ip': self.master,
        })

    @tornado.gen.coroutine
    def start(self):
        '''Dispatches REQs that fire off automatically when the minion starts'''
        self.dispatch({'load': {'fun': None, 'arg': None, 'tgt': self.minion_id, 'load': None, 'jid': None}})

    @tornado.gen.coroutine
    def dispatch(self, load):
        '''Finds appropriate reactions to a PUB message and dispatches them'''
        load = load['load']
        fun = load['fun']
        tgt = load['tgt']

        if tgt != '*' and self.minion_id not in tgt:
            log.trace("Ignoring %s call that targets %s, not me (%s)", fun, tgt, self.minion_id)
            return

        reactions = self.dump_reader.get_reactions(load, self.current_time, self.replacements)
        if reactions:
            self.current_time = reactions[-1]['header']['time']

        ret = yield self.react(load, reactions)

    @tornado.gen.coroutine
    def react(self, load, reactions):
        '''Dispatches reactions in response to some load'''
        for reaction in reactions:
            request = reaction['load']
            if request['cmd'] == '_return' and request.get('fun') == load.get('fun'):
                request['jid'] = load['jid']
                if load.has_key('metadata'):
                    request['metadata']['suma-action-id'] = load['metadata'].get('suma-action-id')
            yield tornado.gen.sleep(reaction['header']['duration'])
            yield self.channel.send(request, timeout=60)
