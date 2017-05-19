'''Simulates a minion via a dump file'''

from distutils.dir_util import mkpath
import hashlib
import os
from uuid import UUID, uuid5

import tornado.gen
import salt.transport.client

from reactor import Reactor

class EvilMinion(object):
    '''Simulates a minion replaying responses from a dump file'''
    def __init__(self, master, minion_id, slowdown_factor, dump_reader, io_loop, keysize):
        self.slowdown_factor = slowdown_factor
        self.dump_reader = dump_reader
        self.io_loop = io_loop

        pki_dir = '/tmp/%s' % minion_id
        mkpath(pki_dir)

        cache_dir = os.path.join(pki_dir, 'cache', 'minion')
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        sock_dir = os.path.join(pki_dir, 'sock', 'minion')
        if not os.path.exists(sock_dir):
            os.makedirs(sock_dir)

        self.opts = {
            'id': minion_id,
            'pki_dir': pki_dir,
            'machine_id': hashlib.md5(minion_id).hexdigest(),
            'uuid': str(uuid5(UUID('d77ed710-0deb-47d9-b053-f2fa2ef78106'), minion_id)),

            'master': master,
            'master_ip': master,
            'master_uri': 'tcp://%s:4506' % master,
            'acceptance_wait_time': 10,
            'acceptance_wait_time_max': 0,
            'zmq_filtering': False,
            'tcp_keepalive': True,
            'tcp_keepalive_idle': 300,
            'tcp_keepalive_cnt': -1,
            'tcp_keepalive_intvl': -1,
            'recon_max': 10000,
            'recon_default': 1000,
            'recon_randomize': True,
            'ipv6': False,
            'zmq_monitor': False,
            'open_mode': False,
            'verify_master_pubkey_sign': False,
            'always_verify_signature': False,
            'keysize': keysize,
            '__role': 'minion',
            'sock_dir': sock_dir,
            'cache_dir': cache_dir,
        }

    @tornado.gen.coroutine
    def start(self):
        '''Opens ZeroMQ sockets, starts listening to PUB events and kicks off initial REQs'''
        factory_kwargs = {'timeout': 60, 'safe': True, 'io_loop': self.io_loop}
        pub_channel = salt.transport.client.AsyncPubChannel.factory(self.opts, **factory_kwargs)
        tok = pub_channel.auth.gen_token('salt')
        yield pub_channel.connect()
        req_channel = salt.transport.client.AsyncReqChannel.factory(self.opts, **factory_kwargs)

        reactor = Reactor(tok, req_channel, self.slowdown_factor, self.dump_reader, self.opts)
        pub_channel.on_recv(reactor.dispatch)
        yield reactor.start()
