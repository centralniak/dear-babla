#!/usr/bin/env python

import os.path

from setuptools import setup


CLASSIFIERS = [
    'Development Status :: 3 - Alpha',
    'Environment :: Console',
    'Intended Audience :: Education',
    'Intended Audience :: End Users/Desktop',
    'License :: OSI Approved :: BSD License',
    'Natural Language :: English',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 3.3',
    'Topic :: Education'
]

REQUIREMENTS = open(os.path.join(os.path.dirname(__file__), 'requirements.txt')).readlines()


setup(
    name='dearbabla',
    description='Helps you learn and memorize English by providing translations and excersises.',
    classifiers=CLASSIFIERS,
    url='https://github.com/centralniak/dear-babla',
    author='Piotr Kilczuk',
    author_email='centralny@centralny.info',
    license='MIT License',

    version='0.0.4',
    install_requires=REQUIREMENTS,
    platforms=['Windows', 'POSIX'],

    entry_points={
        'console_scripts': ['dearbabla=dearbabla:main'],
    },
    py_modules=['dearbabla'],
)
