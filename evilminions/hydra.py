'''Replicates the behavior of a minion many times'''

import logging

import tornado.gen
import zmq

import salt.config
import salt.loader
import salt.payload

from evilminions.hydrahead import HydraHead
from evilminions.utils import fun_call_id

# HACK: turn the trace function into a no-op
# this almost doubles evil-minion's performance
salt.log.mixins.LoggingTraceMixIn.trace = lambda self, msg, *args, **kwargs: None

class Hydra(object):
    '''Spawns HydraHeads, listens for messages coming from the Vampire.'''
    def __init__(self):
        self.current_reactions = []
        self.reactions = {}
        self.last_time = None
        self.serial = salt.payload.Serial({})
        self.log = None

    def start(self, hydra_number, hydra_count, chunk, prefix, offset, ramp_up_delay, slowdown_factor, keysize, semaphore):
        '''Per-process entry point (one per Hydra)'''
        self.hydra_number = hydra_number

        # set up logging
        self.log = logging.getLogger(__name__)
        self.log.debug("Starting Hydra on: %s" % chunk)

        # set up the IO loop
        zmq.eventloop.ioloop.install()
        io_loop = zmq.eventloop.ioloop.ZMQIOLoop.current()

        # set up ZeroMQ connection to the Proxy
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect('ipc:///tmp/evil-minions-pub.ipc')
        socket.setsockopt(zmq.SUBSCRIBE, "")
        stream = zmq.eventloop.zmqstream.ZMQStream(socket, io_loop)
        stream.on_recv(self.update_reactions)

        # Load original settings and grains
        opts = salt.config.minion_config('/etc/salt/minion')
        grains = salt.loader.grains(opts)

        # set up heads!
        first_head_number = chunk[0] if chunk else 0
        delays = [ramp_up_delay * ((head_number - first_head_number) * hydra_count + hydra_number) for head_number in chunk]
        offset_head_numbers = [head_number + offset for head_number in chunk]
        heads = [HydraHead('{}-{}'.format(prefix, offset_head_numbers[i]), io_loop, keysize, opts, grains, delays[i], slowdown_factor, self.reactions) for i in range(len(chunk))]

        # start heads!
        for head in heads:
            io_loop.spawn_callback(head.start)

        semaphore.release()

        io_loop.start()

    @tornado.gen.coroutine
    def update_reactions(self, packed_events):
        '''Called whenever a message from Vampire is received. Updates the internal self.reactions hash to contain reactions that will be mimicked'''
        for packed_event in packed_events:
            event = self.serial.loads(packed_event)

            load = event['load']
            socket = event['header']['socket']
            current_time = event['header']['time']
            self.last_time = self.last_time or current_time
            if socket == 'PUB' and self.reactions == {}:
                self.reactions[fun_call_id(None, None)] = [self.current_reactions]
                self.current_reactions = []
                self.last_time = current_time
            if socket == 'REQ':
                if load['cmd'] == '_auth':
                    continue
                self.current_reactions.append(event)
                if load['cmd'] == '_return':
                    call_id = fun_call_id(load['fun'], load['fun_args'])
                    self.reactions[call_id] = (self.reactions.get(call_id) or []) + [self.current_reactions]
                    self.log.debug("Hydra #{} learned reaction #{} for call: {}".format(self.hydra_number, len(self.reactions[call_id]), call_id))
                    self.current_reactions = []

                event['header']['duration'] = current_time - self.last_time
                self.last_time = current_time
