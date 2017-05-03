import logging
import yaml

log = logging.getLogger(__name__)

class Dump(object):
    def __init__(self, path):
        with open(path, 'r') as f:
            self.dump = list(yaml.safe_load_all(f.read()))

    def find(self, key):
        return self._find(key, self.dump)

    def _find(self, key, dump):
        if type(dump) is dict:
            if dump.has_key(key):
                return dump[key]
            for _, sub_dump in dump.items():
                found = self._find(key, sub_dump)
                if found:
                    return found
        if type(dump) is list:
            for sub_dump in dump:
                found = self._find(key, sub_dump)
                if found:
                    return found

    def replace(self, replacements):
        # turn a "symbolic" replacement list eg. {'machine_id' : '123456'}
        # into an "actual" replacement list eg. {'987654' : '123456'}
        replacements = {self._find(key, self.dump): value for (key, value) in replacements.items()}
        return self._replace(self.dump, replacements)

    def _replace(self, dump, replacements):
        if type(dump) is list:
            return [self._replace(e, replacements) for e in dump]

        if type(dump) is dict:
            return {k: self._replace(v, replacements) for k, v in dump.items()}

        if dump in replacements:
            return replacements[dump]

        return dump

class DumpReader(object):
    def __init__(self, dump_path, replacements):
        self.reactions = {}

        current_reactions = []
        for event in Dump(dump_path).replace(replacements):
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

    def get_reactions_to(self, load):
        call_id = self._fun_call_id(load['fun'], load['arg'] or [])
        result = self.reactions.get(call_id) or []
        if not result:
            log.error("No dump entry corresponding to function %s with parameters %s was found" % call_id)
        return result
