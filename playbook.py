import logging

import dump

log = logging.getLogger(__name__)

class Playbook(object):
    def __init__(self, dump, replacements):
        self.reactions = {}

        current_reactions = []
        for event in dump.replace(replacements):
            load = event['load']
            socket = event['header']['socket']
            if socket == 'PUB' and self.reactions == {}:
                self.reactions[self._fun_call_id(None)] = current_reactions
                current_reactions = []
            if socket == 'REQ':
                if load['cmd'] == '_auth':
                    continue
                current_reactions.append(event)
                if load['cmd'] == '_return':
                    call_id = self._fun_call_id(load['fun'], load['fun_args'])
                    self.reactions[call_id] = current_reactions
                    current_reactions = []

    def _fun_call_id(self, fun, args=[]):
        '''Returns a hashable object that represents the call of a function, with actual parameters'''
        clean_args = [self._zap_kwarg(arg) for arg in args]
        return (fun, self._immutable(clean_args))

    def _zap_kwarg(self, arg):
        if type(arg) is dict:
            return {k: v for k, v in arg.items() if k != '__kwarg__'}
        return arg

    def _immutable(self, data):
        '''Returns an immutable version of any combination of dict, list and hashable types'''
        if type(data) is dict:
            return tuple((k, self._immutable(v)) for k,v in data.items())
        if type(data) is list:
            return tuple(self._immutable(e) for e in data)
        return data

    def reactions_to(self, load):
        call_id = self._fun_call_id(load['fun'], load['arg'] or [])
        result = self.reactions.get(call_id) or []
        if not result:
            log.error("No playbook entry for function %s with parameters %s" % call_id)
        return result
