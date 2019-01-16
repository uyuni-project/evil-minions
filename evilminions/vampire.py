'''Intercepts ZeroMQ traffic'''

import logging
import time

import tornado.gen
from tornado.ioloop import IOLoop
import zmq

from salt.payload import Serial
from salt.transport.zeromq import AsyncZeroMQReqChannel
from salt.transport.zeromq import AsyncZeroMQPubChannel

log = logging.getLogger(__name__)

class Vampire(object):
    '''Intercepts traffic to and from the minion via monkey patching and sends it into the Proxy.'''

    def __init__(self):
        self.serial = Serial({})
        pass

    def attach(self):
        '''Monkey-patches ZeroMQ core I/O class to capture flowing messages.'''
        AsyncZeroMQReqChannel.dump = self.dump
        AsyncZeroMQReqChannel._original_send = AsyncZeroMQReqChannel.send
        AsyncZeroMQReqChannel.send = _dumping_send

        AsyncZeroMQPubChannel.dump = self.dump
        AsyncZeroMQPubChannel._original_on_recv = AsyncZeroMQPubChannel.on_recv
        AsyncZeroMQPubChannel.on_recv = _dumping_on_recv

    def dump(self, load, socket):
        '''Dumps a ZeroMQ message to the Proxy'''

        header = {
            'socket' : socket,
            'time' : time.time(),
        }
        event = {
            'header' : header,
            'load' : load,
        }

        try:
            context = zmq.Context()
            zsocket = context.socket(zmq.PUSH)
            zsocket.connect('ipc:///tmp/evil-minions-pull.ipc')
            io_loop = IOLoop.current()
            stream = zmq.eventloop.zmqstream.ZMQStream(zsocket, io_loop)
            stream.send(self.serial.dumps(event))
            stream.flush()
            stream.close()
        except Exception as exc:
           log.error("Event: {}".format(event))
           log.error("Unable to dump event: {}".format(exc))

@tornado.gen.coroutine
def _dumping_send(self, load, **kwargs):
    '''Dumps a REQ ZeroMQ and sends it'''
    self.dump(load, 'REQ')
    ret = yield self._original_send(load, **kwargs)
    raise tornado.gen.Return(ret)

def _dumping_on_recv(self, callback):
    '''Dumps a PUB ZeroMQ message then handles it'''
    def _logging_callback(load):
        self.dump(load, 'PUB')
        callback(load)
    return self._original_on_recv(_logging_callback)
