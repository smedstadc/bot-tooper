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
        try:
            site = requests.get(url, headers={'User-agent': 'Mozilla/5.0'}, allow_redirects=True, verify=False)
            if site.headers['Content-Type'].startswith('text/html'):
                site.raise_for_status()
                soup = BeautifulSoup(site.content)
                page_titles.append('{}: {}'.format(count, soup.title.string.strip()))
        except Exception:
            print('Could not get title for {}'.format(url))
    return page_titles