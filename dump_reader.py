'''Utils to read dump files'''

import logging
import msgpack

log = logging.getLogger(__name__)

class DumpReader(object):
    def __init__(self, path):
        self.dump = _read_dump(path)

    def get_replacements(self, symbolic_replacements):
        '''Turns a "symbolic" replacement list eg. {'machine_id' : '123456'} into an "actual" replacement list eg. {'987654' : '123456'}'''
        return {_find_in_dump(key, self.dump): value for (key, value) in symbolic_replacements.items()}

    def get_reactions(self, load, current_time, replacements):
        '''Return a list of reactions to a given load from a dump, assuming a current (simulated) time'''
        call_id = _fun_call_id(load['fun'], load['arg'] or [])
        reaction_sets = self.dump.get(call_id) or []
        if not reaction_sets:
            return []

        # if multiple reactions were produced in different points in time, use the first one
        # after the last known timestamp that was already processed
        future_reaction_sets = filter(lambda s: s[0]['header']['time'] >= current_time, reaction_sets)

        # if that cannot be found, use the latest one
        reactions = (future_reaction_sets or [reaction_sets[-1]])[0]

        return _replace_in_dump(replacements, reactions)

def _read_dump(path):
    '''
    Computes a dictionary from a "function call identifier" to reaction lists (sequences of events that followed that call from the dump).
    Note that the dump might contain multiple calls to the same function with identical arguments that resulted in different reactions over time!
    For this reason the function returns a time-ordered list of lists of events.
    '''
    with open(path, 'r') as dump_file:
        dump = msgpack.Unpacker(dump_file)

        result = {}
        current_reactions = []
        last_time = None
        for event in sorted(dump, key=lambda d: d['header']['time']):
            load = event['load']
            socket = event['header']['socket']
            current_time = event['header']['time']
            last_time = last_time or current_time
            if socket == 'PUB' and result == {}:
                result[_fun_call_id(None, None)] = [current_reactions]
                current_reactions = []
            if socket == 'REQ':
                if load['cmd'] == '_auth':
                    continue
                current_reactions.append(event)
                if load['cmd'] == '_return':
                    call_id = _fun_call_id(load['fun'], load['fun_args'])
                    result[call_id] = (result.get(call_id) or []) + [current_reactions]
                    current_reactions = []

            event['header']['duration'] = current_time - last_time
            last_time = current_time

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
        return tuple((k, _immutable(v)) for k, v in sorted(data.items()))
    if isinstance(data, list):
        return tuple(_immutable(e) for e in data)
    return data

def _find_in_dump(key, dump):
    '''Returns a key from a list/dict stucture, recursively'''
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
