'''Implements one evil minion'''

from distutils.dir_util import mkpath
import hashlib
import logging
import os
from uuid import UUID, uuid5

import tornado.gen
import zmq

import salt.transport.client

from evilminions.utils import replace_recursively, fun_call_id

class HydraHead(object):
    '''Replicates the behavior of a minion'''
    def __init__(self, minion_id, io_loop, keysize, opts, grains, ramp_up_delay, slowdown_factor, reactions):
        self.minion_id = minion_id
        self.io_loop = io_loop
        self.ramp_up_delay = ramp_up_delay
        self.slowdown_factor = slowdown_factor
        self.reactions = reactions
        self.current_time = 0

        self.current_jobs = []

        # Compute replacement dict
        self.replacements = {
            grains['id']: minion_id,
            grains['machine_id']: hashlib.md5(minion_id).hexdigest(),
            grains['uuid']: str(uuid5(UUID('d77ed710-0deb-47d9-b053-f2fa2ef78106'), minion_id))
        }

        # Override ID settings
        self.opts = opts.copy()
        self.opts['id'] = minion_id

        # Override calculated settings
        self.opts['master_uri'] = 'tcp://%s:4506' % self.opts['master']
        self.opts['master_ip'] = self.opts['master']

        # Override directory settings
        pki_dir = '/tmp/%s' % minion_id
        mkpath(pki_dir)

        cache_dir = os.path.join(pki_dir, 'cache', 'minion')
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        sock_dir = os.path.join(pki_dir, 'sock', 'minion')
        if not os.path.exists(sock_dir):
            os.makedirs(sock_dir)

        self.opts['pki_dir'] = pki_dir
        self.opts['sock_dir'] = sock_dir
        self.opts['cache_dir'] = cache_dir

        # Override performance settings
        self.opts['keysize'] = keysize
        self.opts['acceptance_wait_time'] = 10
        self.opts['acceptance_wait_time_max'] = 0
        self.opts['zmq_filtering'] = False
        self.opts['tcp_keepalive'] = True
        self.opts['tcp_keepalive_idle'] = 300
        self.opts['tcp_keepalive_cnt'] = -1
        self.opts['tcp_keepalive_intvl'] = -1
        self.opts['recon_max'] = 10000
        self.opts['recon_default'] = 1000
        self.opts['recon_randomize'] = True
        self.opts['ipv6'] = False
        self.opts['zmq_monitor'] = False
        self.opts['open_mode'] = False
        self.opts['verify_master_pubkey_sign'] = False
        self.opts['always_verify_signature'] = False

    @tornado.gen.coroutine
    def start(self):
        '''Opens ZeroMQ sockets, starts listening to PUB events and kicks off initial REQs'''
        self.log = logging.getLogger(__name__)
        yield tornado.gen.sleep(self.ramp_up_delay)
        self.log.info("HydraHead %s started" % self.opts['id'])

        factory_kwargs = {'timeout': 60, 'safe': True, 'io_loop': self.io_loop}
        pub_channel = salt.transport.client.AsyncPubChannel.factory(self.opts, **factory_kwargs)
        self.tok = pub_channel.auth.gen_token('salt')
        yield pub_channel.connect()
        self.req_channel = salt.transport.client.AsyncReqChannel.factory(self.opts, **factory_kwargs)

        pub_channel.on_recv(self.mimic)
        yield self.mimic({'load': {'fun': None, 'arg': None, 'tgt': [self.minion_id], 'tgt_type': 'list', 'load': None, 'jid': None}})

    @tornado.gen.coroutine
    def mimic(self, load):
        '''Finds appropriate reactions to a PUB message and dispatches them'''
        load = load['load']
        fun = load['fun']
        arg = load['arg']
        tgt = load['tgt']
        tgt_type = load['tgt_type']

        if tgt != self.minion_id and (
            (tgt_type == 'glob' and tgt != '*') or
            (tgt_type == 'list' and self.minion_id not in tgt)):
            # ignore call that targets a different minion
            return

        # react in ad-hoc ways to some special calls
        if fun == 'test.ping':
            yield self.react_to_ping(load)
        elif fun == 'saltutil.find_job':
            yield self.react_to_find_job(load)
        elif fun == 'saltutil.running':
            yield self.react_to_running(load)
        else:
            # try to find a suitable reaction and use it
            call_id = fun_call_id(load['fun'], load['arg'] or [])

            reactions = self.get_reactions(call_id)
            while not reactions:
                self.log.debug("No known reaction for call: {}, sleeping 1 second and retrying".format(call_id))
                yield tornado.gen.sleep(1)
                reactions = self.get_reactions(call_id)

            self.current_time = reactions[0]['header']['time']
            yield self.react(load, reactions)

    def get_reactions(self, call_id):
        reaction_sets = self.reactions.get(call_id)
        if not reaction_sets:
            return None

        # if multiple reactions were produced in different points in time, attempt to respect
        # historical order (pick the one which has the lowest timestamp after the last processed)
        future_reaction_sets = filter(lambda s: s[0]['header']['time'] >= self.current_time, reaction_sets)
        if future_reaction_sets:
            return future_reaction_sets[0]

        # if there are reactions but none of them were recorded later than the last processed one, meaning
        # we are seeing an out-of-order request compared to the original ordering, let's be content and return
        # the last known one. Not optimal but hey, Hydras have no crystal balls
        return reaction_sets[-1]

    @tornado.gen.coroutine
    def react(self, load, original_reactions):
        '''Dispatches reactions in response to typical functions'''
        self.current_jobs.append(load)
        reactions = replace_recursively(self.replacements, original_reactions)

        self.current_jobs.append(load)
        for reaction in reactions:
            request = reaction['load']
            if 'tok' in request:
                request['tok'] = self.tok
            if request['cmd'] == '_return' and request.get('fun') == load.get('fun'):
                request['jid'] = load['jid']
                if load.has_key('metadata'):
                    request['metadata']['suma-action-id'] = load['metadata'].get('suma-action-id')
            yield tornado.gen.sleep(reaction['header']['duration'] * self.slowdown_factor)
            yield self.req_channel.send(request, timeout=60)
        self.current_jobs.remove(load)

    @tornado.gen.coroutine
    def react_to_ping(self, load):
        '''Dispatches a reaction to a ping call'''
        request = {
            'cmd': '_return',
            'fun': load['fun'],
            'fun_args': load['arg'],
            'id': self.minion_id,
            'jid': load['jid'],
            'retcode': 0,
            'return': True,
            'success': True,
        }
        yield self.req_channel.send(request, timeout=60)

    @tornado.gen.coroutine
    def react_to_find_job(self, load):
        '''Dispatches a reaction to a find_job call'''
        jobs = filter(lambda j: j['jid'] == load['arg'][0], self.current_jobs)
        ret = dict(jobs[0].items() + {'pid': 1234}.items()) if jobs else {}

        request = {
            'cmd': '_return',
            'fun': load['fun'],
            'fun_args': load['arg'],
            'id': self.minion_id,
            'jid': load['jid'],
            'retcode': 0,
            'return': ret,
            'success': True,
        }
        yield self.req_channel.send(request, timeout=60)

    @tornado.gen.coroutine
    def react_to_running(self, load):
        '''Dispatches a reaction to a running call'''
        request = {
            'cmd': '_return',
            'fun': load['fun'],
            'fun_args': load['arg'],
            'id': self.minion_id,
            'jid': load['jid'],
            'retcode': 0,
            'return': self.current_jobs,
            'success': True,
        }
        yield self.req_channel.send(request, timeout=60)
