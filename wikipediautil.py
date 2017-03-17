# -*- coding: utf-8 -*-

import json
import urllib
from google.appengine.api import urlfetch

API_URL = 'http://en.wikipedia.org/w/api.php'


def _send_query(params):
    res = urlfetch.fetch(
        url=API_URL+"?"+urllib.urlencode(params),
        method=urlfetch.GET
    )
    res = json.loads(res.content)
    return res


def search_titles(query):
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": query,
    }
    return _send_query(params)


def search_contents(titles):
    params = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "rvprop": "content",
        "titles": titles,
    }
    return _send_query(params)
