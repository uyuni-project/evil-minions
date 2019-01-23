'''Relays ZeroMQ traffic between processes'''

import logging
import zmq

def start_proxy(semaphore):
    '''Relays traffic from Vampire to Hydras.'''
    # set up logging
    log = logging.getLogger(__name__)

    # HACK: set up a PULL/PUB proxy
    # https://stackoverflow.com/questions/43129714/zeromq-xpub-xsub-serious-flaw
    log.debug("Starting proxy...")
    context = zmq.Context()
    xsub = context.socket(zmq.PULL)
    xsub.bind('ipc:///tmp/evil-minions-pull.ipc')
    xpub = context.socket(zmq.PUB)
    xpub.bind('ipc:///tmp/evil-minions-pub.ipc')
    log.debug("Proxy ready")
    semaphore.release()
    zmq.proxy(xpub, xsub)
