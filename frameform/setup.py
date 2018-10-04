# -*- coding: utf-8 -*-
"""
Created on Tue May 30 08:32:05 2017

@author: jmccrary
"""

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from frameform import __version__
    
config = {
    'description': 'Create and edit forms with pandas.DataFrames in Jupyter Notebooks',
    'author': 'Joshua McCrary',
    'url': '',
    'download_url': '',
    'author_email': 'jmccrary@spa.com',
    'version': __version__,
    'install_requires': ['IPython', 'ipywidgets', 'numpy', 'pandas'],
    'packages': [],
    'scripts': [],
    'name': 'frameform'
    }
    
setup(**config)
