#!/usr/bin/python

import salt.log
import salt.transport.client

import tornado.gen
import zmq
import zmq.eventloop.ioloop
import logging

from reactor import Reactor

@tornado.gen.coroutine
def connect_master():
    minion_id = opts['id']
    pub_channel = salt.transport.client.AsyncPubChannel.factory(opts, **factory_kwargs)
    tok = pub_channel.auth.gen_token('salt')
    load = {'id': minion_id,
            'cmd': '_minion_event',
            'pretag': None,
            'tok': tok,
            'tag': "minion_start",
            'data': 'Evil minion started up'}
    yield pub_channel.connect()
    req_channel = salt.transport.client.AsyncReqChannel.factory(opts, **factory_kwargs)

    reactor = Reactor(minion_id, req_channel)
    pub_channel.on_recv(lambda load: reactor.dispatch(load))

    yield req_channel.send(load, timeout=60)


salt.log.setup_console_logger(log_level='debug')
log = logging.getLogger(__name__)

opts = {
    'id': 'min.tf.local',
    'pki_dir': '/etc/salt/pki/minion',
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
