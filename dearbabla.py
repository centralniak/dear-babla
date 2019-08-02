#!/usr/bin/env python

import argparse
import os.path
import sqlite3
import sys
import time

import bs4
import requests


BABLA_HTTP_ENDPOINT = 'http://en.bab.la/%(dictionary)s/%(word)s'

DICTIONARY = 'english-polish'

SLEEP_SECONDS = 2


class Cli:

    delay = False
    delete = False
    show_count = False
    store = True
    words = []
    database_location = None

    def __init__(self):
        self._parse_args()
        self.database_location = self._ensure_db_present()

    def _ensure_db_present(self):
        database_location = os.environ.get('DEARBABLA_DB')
        if not database_location or not os.path.exists(database_location):
            raise ValueError('Database not found. DEARBABLA_DB={}'.format(database_location))
        return database_location

    def _parse_args(self):
        parser = argparse.ArgumentParser(
            description='Helps you learn and memorize English by providing translations and excersises.'
        )
        parser.add_argument('words', metavar='N', type=str, nargs='*', help='list of words to operate on')
        parser.add_argument('--count', dest='show_count', action='store_true',
                            help='show how many words were already collected')
        parser.add_argument('--delay', dest='delay', action='store_true',
                            help='waits %d seconds before displaying the translation' % SLEEP_SECONDS)
        parser.add_argument('--delete', dest='delete', action='store_true',
                            help='deletes disappointing translation(s) passed as positional args')
        parser.add_argument('--nostore', dest='store', action='store_false',
                            help='do not store this translation, just query Babla')
        args = parser.parse_args()
        self.delay = args.delay
        self.delete = args.delete
        self.show_count = args.show_count
        self.store = args.store
        self.words = args.words

    def main(self):
        requests_wrapper = RequestsWrapper()
        sql_client = DictionaryModel(self.database_location)

        if self.words:
            if self.delete:
                for word in self.words:
                    sql_client.delete_translations(word)
            else:
                for word in self.words:
                    translations = sql_client.get_translations(word)
                    if not translations:
                        translations = requests_wrapper.get_translations(word)
                        if translations and self.store:
                            sql_client.save_translations(word, translations)
                    print(', '.join(translations))

        elif self.show_count:
            database_count = sql_client.get_count()
            sys.stdout.write('Collected %d words' % database_count)
            sys.stdout.write('\n')

        else:
            random_word = sql_client.get_random_word()
            sys.stdout.write('%s: ' % random_word[0])
            sys.stdout.flush()
            if self.delay:
                time.sleep(SLEEP_SECONDS)
            sys.stdout.write(random_word[1])
            sys.stdout.write('\n')


class DictionaryModel:

    _connection = None
    _c = None

    def __init__(self, database):
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

    def get_count(self):
        result = self._c.execute('SELECT COUNT(*) FROM words')
        return result.fetchone()[0]

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
            'timeout': 8
        }
        new_kwargs.update(kwargs)
        return requests.get(*args, **new_kwargs)

    def get_translations(self, word):
        url = BABLA_HTTP_ENDPOINT % {'dictionary': DICTIONARY, 'word': word}
        response = self._babla_get(url)
        html_soup = bs4.BeautifulSoup(response.text, 'html.parser')
        all_results = set([r.text for r in
            html_soup.select('.content')[0].select('.quick-results .quick-result-entry .sense-group-results a')])
        return all_results


def main():
    cli = Cli()
    cli.main()


if __name__ == '__main__':
    main()
