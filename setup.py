#!/usr/bin/env python

import setuptools
import distutils.command.build
import distutils.command.sdist
import os

setuptools.setup(
    name='git-snake-release',
    version='0.0.1',
    description='Tag a set of git repositories & update setup.py',
    long_description='Tag a set of git repositories & update setup.py',
    long_description_content_type="text/markdown",
    author='Egil Moeller',
    author_email='em@emrld.no',
    url='https://github.com/emerald-geomodelling/git-snake-release',
    packages=setuptools.find_packages(),
    install_requires=[
        "click",
        "pieshell >= 0.1.7",
        "toposort"
    ],
    entry_points = {
        'console_scripts': ['git-snake-release=git_snake_release.main:main'],
    }
    
)
