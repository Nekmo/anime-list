import operator
import os

import time


class Entry(object):
    def __init__(self, entry):
        self.entry = entry
        self.path = entry.path
        self.name = entry.name

    @property
    def is_dir(self):
        return self.entry.is_dir()

    @property
    def is_symlink(self):
        return self.entry.is_symlink()

    @property
    def is_file(self):
        return self.entry.is_file()

    @property
    def mtime(self):
        return self.entry.stat().st_mtime

    @property
    def type(self):
        if self.is_dir:
            return 'dir'
        elif self.is_file:
            return 'file'
        elif self.is_symlink:
            return 'symlink'

    @property
    def msince(self):
        return time.time() - self.mtime

    def analize_filter(self, key, value):
        parts = key.split('__')
        field = getattr(self, parts.pop(0))
        if not parts:
            op = operator.eq
        else:
            op = getattr(operator, parts[0])
        return op(field, value)

    def filter(self, filters):
        for key, value in filters.items():
            if not self.analize_filter(key, value):
                return False
        return True

    def __repr__(self):
        return '<{} "{}">'.format((self.type or 'entry').title(), self.name)


def get_files(directory, filters=None):
    filters = filters or {}
    for entry in os.scandir(directory):
        entry = Entry(entry)
        if entry.is_symlink and not os.path.exists(entry.path):
            # Broken symlinks.
            continue
        if entry.is_dir:
            for subentry in get_files(entry.path, filters):
                yield subentry
        if entry.filter(filters):
            yield entry
