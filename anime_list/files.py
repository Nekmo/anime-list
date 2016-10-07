import mimetypes
import operator
import os
import stat

import time

import six

mimetypes.init()

# Extra mimetypes
mimetypes.add_type('video/x-ogm', '.ogm')


class FakeDirEntry(object):
    _stat = None

    def __init__(self, path):
        self.path = path
        self.name = os.path.split(path)[1]

    def stat(self):
        if not self._stat:
            self._stat = os.stat(self.path)
        return self._stat

    def is_dir(self):
        return stat.S_ISDIR(self.stat().st_mode)

    def is_symlink(self):
        return stat.S_ISLNK(self.stat().st_mode)

    def is_file(self):
        return stat.S_ISREG(self.stat().st_mode)


class Entry(object):
    def __init__(self, entry):
        if isinstance(entry, six.string_types):
            entry = FakeDirEntry(entry)
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
    def mimetype(self):
        return mimetypes.guess_type(self.name)[0]

    @property
    def mime(self):
        return (self.mimetype or '').split('/')[0]

    @property
    def type(self):
        if self.is_dir:
            return 'dir'
        elif self.is_file:
            return 'file'
        elif self.is_symlink:
            return 'symlink'

    def get_entries(self, filters=None, entry_class=None):
        entry_class = entry_class or Entry
        filters = filters or {}
        for file in os.scandir(self.path):
            file = entry_class(file)
            if not file.filter(filters):
                continue
            yield file

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

    def dirname(self):
        return os.path.split(os.path.split(self.path)[0])[1]

    def directory(self):
        return os.path.split(self.path)[0]

    def __lt__(self, other):
        return self.name < other.name

    def __gt__(self, other):
        return self.name > other.name

    def __repr__(self):
        return '<{} "{}">'.format((self.type or 'entry').title(), self.name)


def get_files(directory, filters=None, entry_class=Entry):
    filters = filters or {}
    for entry in os.scandir(directory):
        entry = entry_class(entry)
        if entry.is_symlink and not os.path.exists(entry.path):
            # Broken symlinks.
            continue
        if entry.is_dir:
            for subentry in get_files(entry.path, filters, entry_class):
                yield subentry
        if entry.filter(filters):
            yield entry
