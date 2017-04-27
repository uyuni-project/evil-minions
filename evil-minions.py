#!/usr/bin/python

import hashlib
import logging
import tornado.gen
import zmq
import zmq.eventloop.ioloop

import salt.log
import salt.transport.client

import reactor
import minion_events

@tornado.gen.coroutine
def connect_master():
    minion_id = opts['id']
    pub_channel = salt.transport.client.AsyncPubChannel.factory(opts, **factory_kwargs)
    tok = pub_channel.auth.gen_token('salt')
    yield pub_channel.connect()
    req_channel = salt.transport.client.AsyncReqChannel.factory(opts, **factory_kwargs)

    r = reactor.Reactor(tok, req_channel, 'minion-trace.yml', opts)
    pub_channel.on_recv(lambda load: r.dispatch(load))
    yield r.start()

    yield minion_events.start(minion_id, tok, req_channel)

salt.log.setup_console_logger(log_level='debug')
log = logging.getLogger(__name__)

opts = {
    'id': 'evil-minion.tf.local',
    'pki_dir': '/tmp/evil-minion',
    'machine_id': hashlib.md5('evil-minion.tf.local').hexdigest(),

    # uncomment below to substitute an existing real minion
    # 'id': 'min-1.tf.local',
    # 'machine_id': 'c403e35bcefe9245b077455bc47ad3ac', # cat /etc/machine-id
    # 'pki_dir': '/etc/salt/pki/minion',

    'master': 'suma31pg.tf.local',
    'master_ip': 'suma31pg.tf.local',
    'master_uri': 'tcp://suma31pg.tf.local:4506',
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

zmq.eventloop.ioloop.install()
io_loop = zmq.eventloop.ioloop.ZMQIOLoop.current()

factory_kwargs = {'timeout': 60, 'safe': True, 'io_loop': io_loop}

io_loop.spawn_callback(connect_master)
io_loop.start()
