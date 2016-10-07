import shlex
from collections import OrderedDict
from collections import defaultdict
from datetime import datetime

import re
import os
import subprocess
from flask import Flask
from flask import abort
from flask import render_template
from flask import request

from anime_list.anime import get_animes, get_faileds_by_dir
from anime_list.config import Config
from anime_list.tvshow import TVShowParser
from anime_list.utils import parse_date, to_human_bool, from_human_bool
from ._compat import quote, unescape, unquote

app = Flask(__name__)
app.debug = True
config = Config(os.path.expanduser('~/.config/anime-list/config.yml'))

USE_CACHE = from_human_bool(os.environ.get('USE_CACHE', 'true'))

orders = OrderedDict([
    ('title', {'mdi': 'sort-alphabetical'}),
    ('score', {'default_reversed': True, 'mdi': 'star-half'}),
    ('airing_date', {'function': lambda x: parse_date(x.about['dates'][0] if x.about['dates'] else '1970-01-01',
                                                      force_safe=True), 'mdi': 'calendar'}),
    ('episodes', {'function': lambda x: int(x.about['episodes']), 'mdi': 'sort-numeric'}),
])


# FILES_DIRECTORY = '/media/nekhd/Anime'
FILES_DIRECTORY = '/media/nekraid01/Anime,/media/nekraid02/Anime'


@app.template_filter('clean_synopsis')
def clean_synopsis_filter(s):
    s = unescape(s)
    s = re.sub(r'\[(.+?)\](.+?)\[/\1\]', r'<\1>\2</\1>', s)
    return s


@app.template_filter('filename')
def filename_filter(s):
    return s.split('/')[-1]


@app.template_filter('quote_url')
def quote_url_filter(s):
    return quote(s, safe='')


@app.template_filter('tvshow')
def tvshow_filter(s):
    return TVShowParser(s.name)


@app.route("/")
def animes():
    order_by_id = request.args.get('order_by', 'title')
    order_by_options = orders.get(order_by_id, {})
    use_reverse = from_human_bool(request.args.get('reverse',
                                                   to_human_bool(order_by_options.get('default_reversed', False))))
    sort_function = order_by_options.get('function', lambda x: x.about[order_by_id])
    animes, faileds = get_animes(FILES_DIRECTORY, USE_CACHE)
    animes = sorted(animes, key=sort_function, reverse=use_reverse)
    return render_template('anime-list.html', animes=animes, orders=orders, order_by_id=order_by_id,
                           use_reverse=to_human_bool(use_reverse), browser=request.user_agent.browser)


@app.route("/anime/<anime>/")
def anime(anime):
    anime = unquote(anime)
    animes, faileds = get_animes(FILES_DIRECTORY, USE_CACHE)
    anime = animes.get_by_name(anime)
    if anime is None:
        raise abort(404)
    anime.sort(key=lambda x: x.chapter or 0)
    return render_template('anime.html', anime=anime, config=config)


@app.route("/play", methods=['POST'])
def play():
    player_id = int(request.form['player_id'])
    file = request.form['file']
    player = config['players'][player_id]
    cmd = shlex.split(player['cmd'])
    print(subprocess.check_call(cmd + [file]))
    return ''


@app.route('/lost')
def losts():
    animes, faileds = get_animes(FILES_DIRECTORY, USE_CACHE)
    faileds_by_dir = get_faileds_by_dir(faileds)
    return render_template('lost-list.html', losts=faileds_by_dir, files=faileds)
