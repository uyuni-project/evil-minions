'''Various utility functions'''

def replace_recursively(replacements, dump):
    '''Replaces occurences of replacements.keys with corresponding values in a list/dict structure, recursively'''
    if isinstance(dump, list):
        return [replace_recursively(replacements, e) for e in dump]

    if isinstance(dump, dict):
        return {k: replace_recursively(replacements, v) for k, v in dump.items()}

    if isinstance(dump, str):
        try:
            result = dump
            for original, new in replacements.items():
                result = result.replace(original, new)
            return result
        except UnicodeDecodeError:
            return dump

    if dump in replacements:
        return replacements[dump]

    return dump

def fun_call_id(fun, args):
    '''Returns a hashable object that represents the call of a function, with actual parameters'''
    clean_args = [_zap_uyuni_specifics(_zap_kwarg(arg)) for arg in args or []]
    return (fun, _immutable(clean_args))

def _zap_kwarg(arg):
    '''Takes a list/dict stucture and returns a copy with '__kwarg__' keys removed'''
    if isinstance(arg, dict):
        return {k: v for k, v in arg.items() if k != '__kwarg__'}
    return arg

def _zap_uyuni_specifics(arg):
    '''Takes a list/dict stucture and returns a copy with Uyuni specific varying keys recursively removed'''
    if isinstance(arg, list):
        return [_zap_uyuni_specifics(e) for e in list]
    if isinstance(arg, dict):
        uyuni_repo = arg.get('alias', '').startswith("susemanager:")
        if uyuni_repo:
            return {k: v for k, v in arg.items() if k != 'token'}
        else:
            return {k: _zap_uyuni_specifics(v) for k, v in arg.items()}
    return arg

def _immutable(data):
    '''Returns an immutable version of a list/dict stucture'''
    if isinstance(data, dict):
        return tuple((k, _immutable(v)) for k, v in sorted(data.items()))
    if isinstance(data, list):
        return tuple(_immutable(e) for e in data)
    return data
