from anime_list.files import get_files


def get_animes(dir):
    return get_files(dir, {'type': 'dir'})
