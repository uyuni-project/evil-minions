import yaml
from itertools import ifilter

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
