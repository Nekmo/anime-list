import logging
from collections import defaultdict
from urllib.parse import quote

import os
from file_cache.csv_key_value import KeyValueCache
from file_cache.file import FileCache
from fuzzywuzzy import process
from spice_api import spice

from anime_list.files import get_files, Entry
from anime_list.mal import MalUserList
from anime_list.tvshow import TVShowParser

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
al_cache = FileCache('anime-list')
my_mal_list = MalUserList(creds)

data = my_mal_list.load()
animes_faileds_cache = None


class Anime(Entry, TVShowParser):
    def __init__(self, entry):
        super(Anime, self).__init__(entry)
        self.filename = self.name


class TvshowFiles(list):
    about = None

    def __init__(self, files=(), about=None):
        super(TvshowFiles, self).__init__()
        self.extend(files)
        self.set_about(about)

    def set_about(self, about):
        if about is None:
            return
        self.about = about
        self.my_status = my_mal_list.get_by_id(self.about['id'])

    def to_json(self):
        return {'about': self.about, 'files': [file.path for file in self], 'my_status': self.my_status}


class Tvshows(list):
    def __init__(self, data):
        super(Tvshows, self).__init__(data)

    def get_by_name(self, name):
        for tvshow in self:
            if tvshow.about['title'] == name:
                return tvshow


def get_results_cache_name(path):
    return quote(path.encode('utf-8'), safe='')


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


def get_faileds_by_dir(faileds):
    faileds_by_dir = defaultdict(list)
    for failed in faileds:
        faileds_by_dir[failed.directory()].append(failed)
    return faileds_by_dir


def get_best_result(results, name):
    if not results:
        return
    titles = [result['title'] for result in results]
    title_result = process.extractOne(name, titles)[0]
    for result in results:
        if result['title'] == title_result:
            return result
    return None


def group_by_tvshow(files):
    from anime_list.content_file import ContentFile
    tvshow_files_ids = {}  # MAL id: TvshowFiles(about=tvshow_data)
    tvshows = {}  # tvshow name (processed): TvshowFiles(about=tvshow_data)
    failed_tvshow_names = []
    faileds = []
    content_files = {}
    for file in files:
        tvshow_data = None
        content_file_path = os.path.join(file.directory(), '.content.yml')
        content_file = content_files.get(content_file_path, ContentFile(content_file_path, read_enabled=False))
        content_files[content_file_path] = content_file
        for tvshow in filter(lambda x: x, [content_file.search('animes', file.name), file.tvshow,
                                           file.dirname(), TVShowParser(file.dirname()).tvshow]):
            if tvshow not in failed_tvshow_names and tvshow not in tvshows:
                # No se ha realizado antes una búsqueda por este término de búsqueda en esta
                # sesión (no se encuentra bien en búsquedas exitosas o búsquedas fallidas)
                results = search(tvshow)
                tvshow_data = get_best_result(results, tvshow) or tvshow_data
                logger.info('Local anime {} -> {} ANN anime'.format(tvshow, tvshow_data['title'])) if results else None
            elif tvshow in tvshows:
                # La búsqueda se encuentra en búsquedas exitosas, así que se utiliza el
                # TvshowFiles ya existente.
                tvshow_data = tvshows[tvshow]
            if tvshow_data:
                # Se ha conseguido un tvshow_data, bien porque la búsqueda ha sido exitosa, bien
                # porque era ya una realizada.
                break
            if tvshow not in failed_tvshow_names:
                # Llegados a este punto, es una búsqueda fallida, pero además es una que no está
                # registrada en failed_tvshow_names
                logger.warning('Not tvshow for {}. File: {}'.format(tvshow, file.name))
                failed_tvshow_names.append(tvshow)
            # En este punto, significa que no se ha conseguido un tvshow_data. Se intenta con el
            # siguiente tvshow si lo hubiese.
        if tvshow not in tvshows and tvshow_data:
            # Ha habido éxito y no existe un TvshowFiles previo.
            tvshows[tvshow] = tvshow_files_ids.get(tvshow_data['id'], TvshowFiles(about=tvshow_data))
            tvshow_files_ids[tvshow_data['id']] = tvshows[tvshow]
        if tvshow_data:
            # Ha habido éxito y existe un TvshowFiles previo. Se utiliza.
            tvshows[tvshow].append(file)
        else:
            # No ha habido éxito. Se añade a la lista de huérfanos.
            faileds.append(file)
    return Tvshows(tvshow_files_ids.values()), faileds


def load_cache(directory):
    cache = al_cache.load(get_results_cache_name(directory))
    if not cache:
        return
    tvshows = [TvshowFiles([Anime(x) for x in tvshow['files']], tvshow['about']) for tvshow in cache['tvshows']]
    faileds = [Entry(x) for x in cache['faileds']]
    return Tvshows(tvshows), faileds


def save_cache(directory, tvshows, faileds):
    data = {
        'tvshows': [tvshow.to_json() for tvshow in tvshows],
        'faileds': [failed.path for failed in faileds],
    }
    al_cache.save(data, get_results_cache_name(directory))


def get_dirs(paths):
    for path in paths.split(','):
        for file in get_files(path, {'type': 'dir'}):
            yield file


def get_animes(path, use_cache=True):
    global animes_faileds_cache
    cache = None
    if use_cache and animes_faileds_cache is not None:
        return animes_faileds_cache
    if use_cache:
        cache = load_cache(path)
        animes_faileds_cache = cache
    if not cache:
        dirs = get_dirs(path)
        files = []
        for directory in dirs:
            files.extend(sorted(list(directory.get_entries({'type': 'file', 'mime': 'video'}, Anime))))
        tvshows, faileds = group_by_tvshow(files)
        animes_faileds_cache = tvshows, faileds
        save_cache(path, tvshows, faileds)
        return tvshows, faileds
    else:
        return cache
