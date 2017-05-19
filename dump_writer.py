'''Classes to write dump files'''

import ast
import time
import yaml
import logging

import tornado.gen

from salt.transport.zeromq import AsyncZeroMQReqChannel
from salt.transport.zeromq import AsyncZeroMQPubChannel

log = logging.getLogger(__name__)


class DumpWriter(object):
    '''Dumps ZeroMQ I/O messages into a Yaml file.'''

    def __init__(self, trace_path):
        self.dump_file = open(trace_path, 'w+')

    def attach(self):
        '''Monkey-patches ZeroMQ core I/O classes to dump exchanged messages to a Yaml file.'''
        AsyncZeroMQReqChannel.dump = self.dump
        AsyncZeroMQReqChannel.send_original = AsyncZeroMQReqChannel.send
        AsyncZeroMQReqChannel.send = _logging_send

        AsyncZeroMQPubChannel.dump = self.dump
        AsyncZeroMQPubChannel.on_recv_original = AsyncZeroMQPubChannel.on_recv
        AsyncZeroMQPubChannel.on_recv = _logging_on_recv

    def dump(self, load, socket):
        '''Dumps a ZeroMQ message, socket identifies the channel and direction'''
        header = {
            'socket' : socket,
            'time' : time.time(),
        }
        event = {
            'header' : header,
            'load' : load,
        }

        try:
           # Event sanization
           event = ast.literal_eval(str(event))
           yml_event = yaml.safe_dump(event, default_flow_style=False)
           self.dump_file.write("---\n")
           self.dump_file.write(yml_event)
           self.dump_file.flush()
        except Exception as exc:
           log.error("Event: {}".format(event))
           log.error("Unable to dump event: {}".format(exc))

@tornado.gen.coroutine
def _logging_send(self, load, **kwargs):
    '''Sends a REQ ZeroMQ message logging it and the corresponding REP to a dump file'''
    self.dump(load, 'REQ')
    ret = yield self.send_original(load, **kwargs)
    self.dump(ret, 'REP')
    raise tornado.gen.Return(ret)

def _logging_on_recv(self, callback):
    '''Handles a PUB ZeroMQ message and additionally logs it to a dump file'''
    def _logging_callback(load):
        self.dump(load, 'PUB')
        callback(load)
    return self.on_recv_original(_logging_callback)
