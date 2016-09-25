from spice_api import spice

from anime_list.utils import safe_int


class MyStatus(dict):
    statues = {1: 'watching', 2: 'completed', 3: 'onhold', 4: 'dropped', 6: 'plantowatch'}
    fields = ['status_id', 'status', 'score', 'rewatches', 'rewatch_ep', 'episodes']

    def __init__(self, data):
        super(MyStatus, self).__init__()
        self.data = data
        self.status_id = int(self.data.status)
        self.status = self.statues[self.status_id]
        self.score = safe_int(self.data.score, None)
        self.rewatches = safe_int(self.data.rewatches, None)
        self.rewatch_ep = safe_int(self.data.rewatch_ep, None)
        self.episodes = safe_int(self.data.episodes, None)
        for field in self.fields:
            self[field] = getattr(self, field)


class MalUserList(object):
    by_status = None
    all = None

    def __init__(self, auth, username=None, medium='anime'):
        self.auth = auth
        self.username = username or auth[0]
        self.medium = medium

    def load(self):
        if self.by_status:
            return
        self.by_status = spice.get_list(spice.get_medium('anime'), self.username, self.auth)
        self.all = []
        for medias in self.by_status.medium_list.values():
            self.all.extend(medias)

    def filter(self, **kwargs):
        def _filter(x):
            for key, value in kwargs.items():
                if getattr(x, key) != value:
                    return False
            return True
        return filter(_filter, self.all)


    def get_by_name(self, name):
        self.load()

    def get_by_id(self, id):
        self.load()
        results = list(self.filter(id=id))
        if not results:
            return None
        return MyStatus(results[0])

