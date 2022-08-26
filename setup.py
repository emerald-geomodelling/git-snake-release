#!/usr/bin/env python

import setuptools
import distutils.command.build
import distutils.command.sdist
import os

setuptools.setup(
    name='git-snake-release',
    version='0.7.0',
    description='',
    long_description='',
    long_description_content_type="text/markdown",
    author='Egil Moeller',
    author_email='em@emeraldgeo.no',
    url='https://github.com/EMeraldGeo/git-snake-release',
    packages=setuptools.find_packages(),
    install_requires=[
    ],
)
