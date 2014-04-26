#!/usr/bin/env python3
""" url.py
    Returns a list of page titles for a given list of urls.

"""

from bs4 import BeautifulSoup
import requests


def get_url_titles(urls):
    """Returns a list of page titles for a given list of urls."""
    page_titles = []
    for url in urls:
        try:
            site = requests.get(url, headers={'User-agent': 'Mozilla/5.0'}, allow_redirects=True, verify=False)
            if site.headers['Content-Type'].startswith('text/html'):
                soup = BeautifulSoup(site.content)
                page_titles.append(soup.title.string.strip())
        except Exception as e:
            print('Failed attempting to get title for {}'.format(url))
            print('ERROR: {}'.format(e))
    return page_titles