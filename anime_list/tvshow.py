import re

from anime_list.utils import int_or_float


class TVShowParser(object):
    _name = None
    _tvshow = None
    _seasson = None
    _chapter = None
    _extra = None

    def __init__(self, filename):
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
        name = re.sub(r'[\b ](hdtv|hd|dvd|bd|720p|1080p|tv|rip|dbrip|dvdrip)(?:\Z|\b)', '', name, flags=re.IGNORECASE)
        # Eliminar aquello que sea una "v" seguido de un número (versiones)
        name = re.sub('v[0-9]', '', name, flags=re.IGNORECASE)
        # Sustituir puntos y barras bajas por espacios
        name = re.sub('\.|_', ' ', name)
        # Eliminar guiones separadores
        # name = name.replace(' - ', ' ')
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
        tvshow = re.sub('(\d+)', '', self.cleaned_name)
        tvshow = tvshow.replace('  ', ' ')
        tvshow = re.sub(r'[\b ](op|ed|opening|ending)(?:\Z|\b)', '', tvshow, flags=re.IGNORECASE)
        # Eliminamos lo que se encuentra tras un " - ".
        tvshow = tvshow.split(' - ', 1)[0]
        # Eliminar espacio del comienzo del nombre
        if tvshow.startswith(' '): tvshow = tvshow[1:]
        # Eliminar espacio del final del nombre
        if tvshow.endswith(' '): tvshow = tvshow[:-1]
        return tvshow

    def get_seasson(self):
        seasson = re.findall('(\d+)', self.cleaned_name)
        if len(seasson) > 1:
            return seasson[0]
        return False

    def get_chapter(self):
        chapter = re.findall('(\d+)', self.cleaned_name)
        chapter = int_or_float(chapter[-1]) if len(chapter) else None
        return chapter

    def get_extra(self):
        match = re.findall(r'[\b ](op|ed|opening|ending)(?:\Z|\b)', self.cleaned_name, flags=re.IGNORECASE)
        return match[0] if match else ''

    @property
    def cleaned_name(self):
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

    @property
    def extra(self):
        if self._extra is None: self._extra = self.get_extra()
        return self._extra
