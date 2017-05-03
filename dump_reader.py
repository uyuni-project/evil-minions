'''Classes to read dump files'''

import logging
import yaml

log = logging.getLogger(__name__)

class DumpReader(object):
    '''Reads a dump file and parses it into a "request id to response" dictionary'''
    def __init__(self, path, replacements):
        with open(path, 'r') as dump_file:
            raw_dump = list(yaml.safe_load_all(dump_file.read()))

            # turn a "symbolic" replacement list eg. {'machine_id' : '123456'}
            # into an "actual" replacement list eg. {'987654' : '123456'}
            actual_replacements = {_find_in_dump(key, raw_dump): value for (key, value) in replacements.items()}

            dump = _replace_in_dump(actual_replacements, raw_dump)
            self.reactions = _compute_reactions(dump)

    def get_reactions_to(self, load):
        '''Returns reactions to a certain PUB load, looking up the same function signature in the dump data'''
        call_id = _fun_call_id(load['fun'], load['arg'] or [])
        result = self.reactions.get(call_id) or []
        if not result:
            log.error("No dump entry corresponding to function %s with parameters %s was found", call_id[0], call_id[1])
        return result

def _compute_reactions(dump):
    '''Computes a function id to reactions dictionary by re-playing event history from the dump'''
    result = {}

    current_reactions = []
    for event in dump:
        load = event['load']
        socket = event['header']['socket']
        if socket == 'PUB' and result == {}:
            result[_fun_call_id(None, None)] = current_reactions
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

def _fun_call_id(fun, args):
    '''Returns a hashable object that represents the call of a function, with actual parameters'''
    clean_args = [_zap_kwarg(arg) for arg in args or []]
    return (fun, _immutable(clean_args))

def _zap_kwarg(arg):
    '''Takes a list/dict stucture and returns a copy with '__kwarg__' keys recursively removed'''
    if isinstance(arg, dict):
        return {k: v for k, v in arg.items() if k != '__kwarg__'}
    return arg

def _immutable(data):
    '''Returns an immutable version of a list/dict stucture'''
    if isinstance(data, dict):
        return tuple((k, _immutable(v)) for k, v in data.items())
    if isinstance(data, list):
        return tuple(_immutable(e) for e in data)
    return data

def _find_in_dump(key, dump):
    '''Returns a key from a list/dict stucture'''
    if isinstance(dump, dict):
        if dump.has_key(key):
            return dump[key]
        for _, sub_dump in dump.items():
            found = _find_in_dump(key, sub_dump)
            if found:
                return found
    if isinstance(dump, list):
        for sub_dump in dump:
            found = _find_in_dump(key, sub_dump)
            if found:
                return found

def _replace_in_dump(replacements, dump):
    '''Replaces occurences of replacements.keys with corresponding values in a list/dict structure, recursively'''
    if isinstance(dump, list):
        return [_replace_in_dump(replacements, e) for e in dump]

    if isinstance(dump, dict):
        return {k: _replace_in_dump(replacements, v) for k, v in dump.items()}

    if dump in replacements:
        return replacements[dump]

    return dump
