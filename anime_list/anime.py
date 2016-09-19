import re
from collections import defaultdict

import logging

from anime_list.files import get_files
from spice_api import spice
from file_cache.csv_key_value import KeyValueCache
from file_cache.file import FileCache

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


creds = spice.load_auth_from_file('mal_auth')
words_cache = KeyValueCache('mal')
file_cache = FileCache('mal')


class TVShowName(object):
    def __init__(self, filename):
        self._name = None
        self._tvshow = None
        self._seasson = None
        self._chapter = None
        self.filename = filename

    def get_name(self):
        name = self.filename
        if '.' in name: name = '.'.join(name.split('.')[:-1])
        # Elimnar aquello que se encuentre tras el CRC
        name = re.sub('\[[0-9-A-Fa-f]{8}\].+', '', name)
        # Eliminar lo que se encuentre entre corchetes
        name = re.sub('\[[^\]]+\]', '', name)
        # Eliminar lo que se encuentre entre paréntesis
        name = re.sub('\(.+?\)', '', name)
        # Eliminar palabras sobre calidad de vídeo
        name = re.sub('\b(hd|dvd|bd|720p|1080p|tv|rip|dbrip)\b', '', name, flags=re.IGNORECASE)
        # Eliminar aquello que sea una "v" seguido de un número (versiones)
        name = re.sub('v[0-9]', '', name, flags=re.IGNORECASE)
        # Sustituir puntos y barras bajas por espacios
        name = re.sub('\.|_', ' ', name)
        # Eliminar guiones separadores
        name = name.replace(' - ', ' ')
        # Eliminar las almohadillas
        name = re.sub('#', ' ', name)
        # Eliminar espacios múltiples, y sustiuir por 1
        name = re.sub(' +', ' ', name)
        # Eliminar espacio del comienzo del nombre
        name = name.lstrip(' ')
        # Eliminar espacio del final del nombre
        name = name.rstrip(' ')
        # Poner como título el nombre
        name = name.title()
        return name

    def get_tvshow(self):
        tvshow = re.sub('(\d+)', '', self.name)
        tvshow = tvshow.replace('  ', ' ')
        tvshow = re.sub('\b(op|ed|opening|ending)\b', '', tvshow, flags=re.IGNORECASE)
        # Eliminar espacio del comienzo del nombre
        if tvshow.startswith(' '): tvshow = tvshow[1:]
        # Eliminar espacio del final del nombre
        if tvshow.endswith(' '): tvshow = tvshow[:-1]
        return tvshow

    def get_seasson(self):
        seasson = re.findall('(\d+)', self.name)
        if len(seasson) > 1:
            return seasson[0]
        return False

    def get_chapter(self):
        chapter = re.findall('(\d+)', self.name)
        chapter = chapter[-1]
        return chapter

    @property
    def name(self):
        if self._name is None: self._name = self.get_name()
        return self._name

    @property
    def seasson(self):
        if self._seasson is None: self._seasson = self.get_seasson()
        return self._seasson

    @property
    def tvshow(self):
        if self._tvshow is None: self._tvshow = self.get_tvshow()
        return self._tvshow

    @property
    def chapter(self):
        if self._chapter is None: self._chapter = self.get_chapter()
        return self._chapter


class TvshowFiles(list):
    def __init__(self, files=(), about=None):
        super(TvshowFiles, self).__init__()
        self.extend(files)
        self.about = about


def search(query):
    cache = words_cache.load(query)
    if cache:
        # Load from cache
        files = [int(x) for x in cache['value'].split(',') if x]
        return [file_cache.load(x) for x in files]
    results = spice.search(query, spice.get_medium('anime'), creds)
    results = [result.to_json() for result in results]
    # Save to cache
    words_cache.save(query, ','.join([str(x['id']) for x in results]))
    for result in results:
        file_cache.save(result, result['id'], 'json')
    return results


def group_by_tvshow(files):
    tvshow_files_ids = {}  # MAL id: TvshowFiles(about=tvshow_data)
    tvshows = {}  # tvshow name (processed): TvshowFiles(about=tvshow_data)
    faileds = []
    files_tvshows = [{'tvshow': TVShowName(x.name), 'file': x} for x in files]
    for file_tvshow in files_tvshows:
        tvshow_data = None
        # results = search(tvshow, 'anime') if not tvshow in faileds else None
        results = None
        for tvshow in [file_tvshow['tvshow'].tvshow, file_tvshow['file'].dirname()]:
            # TODO: el tvshow NO debe ser el título que se usará al final.
            if tvshow not in faileds and not tvshow in tvshows:
                results = search(tvshow)
            elif tvshow in tvshows:
                tvshow_data = tvshows[tvshow]
                break
            if results:
                tvshow_data = results[0]
                logger.info('Local anime {} -> {} ANN anime'.format(tvshow, tvshow_data['title']))
                break
            elif not tvshow_data and not tvshow in faileds:
                faileds.append(tvshow)
                logger.warning('Not tvshow for {}'.format(tvshow))
        if tvshow not in tvshows and tvshow_data:
            tvshows[tvshow] = tvshow_files_ids.get(tvshow_data['id'], TvshowFiles(about=tvshow_data))
        if tvshow_data:
            tvshows[tvshow].append(tvshow)
    return tvshow_files_ids.values()


def get_animes(dir):
    dirs = get_files(dir, {'type': 'dir'})
    files = []
    for directory in dirs:
        files.extend(sorted(list(directory.get_entries({'type': 'file'}))))
    return group_by_tvshow(files)
