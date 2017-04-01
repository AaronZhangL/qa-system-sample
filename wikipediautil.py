# -*- coding: utf-8 -*-

import json
import urllib
from google.appengine.api import urlfetch
from bs4 import BeautifulSoup

API_URL = 'http://en.wikipedia.org/w/api.php'


def _send_query(params):
    res = urlfetch.fetch(
        url="{0}?{1}".format(API_URL, urllib.urlencode(params)),
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
        'rvparse': "",
        "titles": titles,
    }
    res_contents = _send_query(params)
    wikipedia_content = res_contents["query"]["pages"].values()[0]["revisions"][0]["*"]
    wikipedia_content = BeautifulSoup(wikipedia_content, "html.parser").get_text()
    wikipedia_content = wikipedia_content.replace("\n", "  ")
    wikipedia_content = wikipedia_content.replace("\"", "")
    return wikipedia_content
