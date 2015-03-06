#!/usr/bin/env python

import os.path
import sqlite3
import sys

import bs4
import requests


BABLA_HTTP_ENDPOINT = 'http://en.bab.la/%(dictionary)s/%(word)s'

DICTIONARY = 'english-polish'


class DictionaryModel:

    _connection = None
    _c = None

    def __init__(self, database=None):
        if database is None:
            database = os.path.join(os.path.dirname(__file__), 'dearbabla.db')
        self._connection = sqlite3.connect(database)
        self._c = self._connection.cursor()
        self._ensure_tables()

    def _ensure_tables(self):
        try:
            self._c.execute('CREATE TABLE words (dictionary TEXT, word TEXT, translations TEXT)')
        except sqlite3.OperationalError:
            pass  # table already exists

    def delete_translations(self, word):
        result = self._c.execute('DELETE FROM words WHERE dictionary=? AND word=?', (DICTIONARY, word, ))
        self._connection.commit()
        return result

    def get_random_word(self):
        result = self._c.execute('SELECT word, translations FROM words WHERE dictionary=? ORDER BY RANDOM()', (DICTIONARY, ))
        return result.fetchone()

    def get_translations(self, word):
        result = self._c.execute('SELECT translations FROM words WHERE dictionary=? AND word=?', (DICTIONARY, word, ))
        for row in result:
            return row[0].split(', ')

    def save_translations(self, word, translations):
        translations = ', '.join(translations)
        self._c.execute('INSERT INTO words VALUES (?, ?, ?)', (DICTIONARY, word, translations, ))
        self._connection.commit()


class RequestsWrapper:

    def _babla_get(self, *args, **kwargs):
        """
        Get babla request with prepared Chrome headers

        :return: response
        """
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.8,en-US;q=0.6,pl;q=0.4',
            'Referer': 'http://en.bab.la/',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.115 Safari/537.36'
        }
        new_kwargs = {
            'headers': headers,
            'timeout': 2
        }
        new_kwargs.update(kwargs)
        return requests.get(*args, **new_kwargs)

    def get_translations(self, word):
        url = BABLA_HTTP_ENDPOINT % {'dictionary': DICTIONARY, 'word': word}
        response = self._babla_get(url)
        html_soup = bs4.BeautifulSoup(response.text)
        all_results = [r.text for r in html_soup.select('.result-block .result-right .result-link')]
        return all_results


def main():
    requests_wrapper = RequestsWrapper()
    sql_client = DictionaryModel()

    if len(sys.argv) > 1:
        if sys.argv[1] == '--delete':
            for word in sys.argv[2:]:
                sql_client.delete_translations(word)
        else:
            for word in sys.argv[1:]:
                translations = sql_client.get_translations(word)
                if not translations:
                    translations = requests_wrapper.get_translations(word)
                    sql_client.save_translations(word, translations)
                print(', '.join(translations))

    else:
        random_word = sql_client.get_random_word()
        print('%s:  %s' % random_word)


if __name__ == '__main__':
    main()
