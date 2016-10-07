import os

from anime_list.anime import get_animes, get_faileds_by_dir
from anime_list.config import Config
from anime_list.utils import from_human_bool

from ._compat import quote


USE_CACHE = from_human_bool(os.environ.get('USE_CACHE', 'true'))


class ContentFile(Config):

    def add_lost(self, title):
        lost = self.get('lost', [])
        if title in lost:
            return
        lost.append(title)
        self['lost'] = lost

    def add_losts(self, titles):
        for title in titles:
            self.add_lost(title)

    def search(self, type, file):
        self.read()
        if type not in self:
            return
        if not isinstance(self[type], dict):
            return self[type]
        file = os.path.split(file)[-1]
        for name, files in self[type].items():
            if file in files:
                return name


def generate_faileds(path):
    tvshows, faileds = get_animes(path, USE_CACHE)
    faileds_by_dir = get_faileds_by_dir(faileds)
    for directory, files in faileds_by_dir.items():
        path = os.path.join(directory, '.content.yml')
        print('file://{} - {} ({})'.format(quote(path), os.path.split(directory)[-1], len(files)))
        content = ContentFile(path)
        content.add_losts([x.name for x in files])
        content.write()
