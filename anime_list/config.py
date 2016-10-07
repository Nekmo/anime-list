import os
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


class Config(dict):
    _read = False

    def __init__(self, file, **kwargs):
        read_enabled = kwargs.pop('read_enabled', True)
        super(Config, self).__init__(**kwargs)
        self.file = file
        if read_enabled:
            self.read()

    def read(self):
        if self._read:
            return
        self._read = True
        if not os.path.exists(self.file):
            return
        data = load(open(self.file), Loader)
        # if not isinstance(data, dict):
        #     data = {}
        self.update(data)

    def write(self):
        dump(dict(self), open(self.file, 'w'), Dumper, default_flow_style=False, width=180)
