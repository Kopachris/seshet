#!/usr/bin/env python3

"""Seshet - Modular, dynamic IRC bot"""

from setuptools import setup
from os import path


long_description = open(
    path.join(
        path.dirname(__file__),
        'README.md'
    )
).read()

setup(
    name='seshet',
    version='0.1.0',
    url='https://github.com/kopachris/seshet',
    license='BSD',
    author='Christopher Koch',
    author_email='ch_koch@outlook.com',
    description='Modular, dynamic IRC bot',
    long_description=long_description,  # update later
    packages=['seshet'],
    install_requires=[
        'ircutils3',
        'pydal',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Operating System :: OS Independent',

        'License :: OSI Approved :: BSD License',

        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',

        'Topic :: Communications :: Chat :: Internet Relay Chat',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)