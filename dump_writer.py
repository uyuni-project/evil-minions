import yaml
import time

import tornado.gen

from salt.transport.zeromq import AsyncZeroMQReqChannel
from salt.transport.zeromq import AsyncZeroMQPubChannel

class DumpWriter(object):
    '''Monkey-patches ZeroMQ core I/O classes to dump exchanged messages to a Yaml file.'''
    def __init__(self, trace_path):
        self.dump_file = open(trace_path, 'w+')

    def install(self):
        AsyncZeroMQReqChannel.dump = self.dump
        AsyncZeroMQReqChannel.send_original = AsyncZeroMQReqChannel.send
        AsyncZeroMQReqChannel.send = _logging_send

        AsyncZeroMQPubChannel.dump = self.dump
        AsyncZeroMQPubChannel.on_recv_original = AsyncZeroMQPubChannel.on_recv
        AsyncZeroMQPubChannel.on_recv = _logging_on_recv

    def dump(self, load, socket):
        header = {
            'socket' : socket,
            'time' : time.time(),
        }
        event = {
            'header' : header,
            'load' : load,
        }
        self.dump_file.write("---\n")
        self.dump_file.write(yaml.safe_dump(event, default_flow_style=False))
        self.dump_file.flush()

@tornado.gen.coroutine
def _logging_send(self, load, **kwargs):
    self.dump(load, 'REQ')
    ret = yield self.send_original(load, **kwargs)
    self.dump(ret, 'REP')
    raise tornado.gen.Return(ret)

def _logging_on_recv(self, callback):
    def _logging_callback(load):
        self.dump(load, 'PUB')
        callback(load)
    return self.on_recv_original(_logging_callback)
