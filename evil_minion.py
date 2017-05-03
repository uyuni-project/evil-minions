from distutils.dir_util import mkpath
import hashlib

import tornado.gen
import salt.transport.client

from reactor import Reactor

class EvilMinion(object):
    '''Simulates a minion replaying responses from a dump file'''
    def __init__(self, master, minion_id, dump_path, io_loop):
        self.io_loop = io_loop
        self.dump_path = dump_path

        pki_dir = '/tmp/%s' % minion_id
        mkpath(pki_dir)

        self.opts = {
            'id': minion_id,
            'pki_dir': pki_dir,
            'machine_id': hashlib.md5(minion_id).hexdigest(),

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
            'keysize': 2048,
        }

    @tornado.gen.coroutine
    def start(self):
        factory_kwargs = {'timeout': 60, 'safe': True, 'io_loop': self.io_loop}
        pub_channel = salt.transport.client.AsyncPubChannel.factory(self.opts, **factory_kwargs)
        tok = pub_channel.auth.gen_token('salt')
        yield pub_channel.connect()
        req_channel = salt.transport.client.AsyncReqChannel.factory(self.opts, **factory_kwargs)

        reactor = Reactor(tok, req_channel, self.dump_path, self.opts)
        pub_channel.on_recv(lambda load: reactor.dispatch(load))
        yield reactor.start()
