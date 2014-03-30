#!/usr/bin/env python3
""" url.py
    Returns a list of page titles for a given list of urls.

"""

from bs4 import BeautifulSoup
import requests


def get_url_titles(urls):
    """Returns a list of page titles for a given list of urls."""
    page_titles = []
    count = 0
    for url in urls:
        count += 1
        site = requests.get(url)
        try:
            if site.headers['Content-Type'].startswith('text/html'):
                site.raise_for_status()
                soup = BeautifulSoup(site.content)
                page_titles.append('{}: {}'.format(count, soup.title.string.strip()))
        except requests.exceptions.HTTPError:
            page_titles.append('{}: 404\'d!'.format(count))
    return page_titles