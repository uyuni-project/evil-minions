import logging
import yaml

log = logging.getLogger(__name__)

class DumpReader(object):
    def __init__(self, path, replacements):
        with open(path, 'r') as f:
            raw_dump = list(yaml.safe_load_all(f.read()))

            # turn a "symbolic" replacement list eg. {'machine_id' : '123456'}
            # into an "actual" replacement list eg. {'987654' : '123456'}
            actual_replacements = {_find_in_dump(key, raw_dump): value for (key, value) in replacements.items()}

            dump = _replace_in_dump(actual_replacements, raw_dump)
            self.reactions = _compute_reactions(dump)

    def get_reactions_to(self, load):
        call_id = _fun_call_id(load['fun'], load['arg'] or [])
        result = self.reactions.get(call_id) or []
        if not result:
            log.error("No dump entry corresponding to function %s with parameters %s was found" % call_id)
        return result

def _compute_reactions(dump):
    result = {}

    current_reactions = []
    for event in dump:
        load = event['load']
        socket = event['header']['socket']
        if socket == 'PUB' and result == {}:
            result[_fun_call_id(None)] = current_reactions
            current_reactions = []
        if socket == 'REQ':
            if load['cmd'] == '_auth':
                continue
            current_reactions.append(event)
            if load['cmd'] == '_return':
                call_id = _fun_call_id(load['fun'], load['fun_args'])
                result[call_id] = current_reactions
                current_reactions = []

    return result

def _fun_call_id(fun, args=[]):
    '''Returns a hashable object that represents the call of a function, with actual parameters'''
    clean_args = [_zap_kwarg(arg) for arg in args]
    return (fun, _immutable(clean_args))

def _zap_kwarg(arg):
    if type(arg) is dict:
        return {k: v for k, v in arg.items() if k != '__kwarg__'}
    return arg

def _immutable(data):
    '''Returns an immutable version of any combination of dict, list and hashable types'''
    if type(data) is dict:
        return tuple((k, _immutable(v)) for k,v in data.items())
    if type(data) is list:
        return tuple(_immutable(e) for e in data)
    return data

def _find_in_dump(key, dump):
    if type(dump) is dict:
        if dump.has_key(key):
            return dump[key]
        for _, sub_dump in dump.items():
            found = _find_in_dump(key, sub_dump)
            if found:
                return found
    if type(dump) is list:
        for sub_dump in dump:
            found = _find_in_dump(key, sub_dump)
            if found:
                return found

def _replace_in_dump(replacements, dump):
    if type(dump) is list:
        return [_replace_in_dump(replacements, e) for e in dump]

    if type(dump) is dict:
        return {k: _replace_in_dump(replacements, v) for k, v in dump.items()}

    if dump in replacements:
        return replacements[dump]

    return dump
