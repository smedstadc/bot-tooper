__author__ = 'Corey'

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
            site.raise_for_status()
            soup = BeautifulSoup(site.content)
            page_titles.append('{}: {}'.format(count, soup.title.string))
        except requests.exceptions.HTTPError:
            page_titles.append('{}: 404\'d!'.format(count))
    return page_titles