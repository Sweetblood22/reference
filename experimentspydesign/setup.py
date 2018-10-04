# -*- coding: utf-8 -*-
"""
Created on Tue May 1 21:32:05 2018

@author: jmccrary
"""

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
    
config = {
    'description': 'Define Factors for experiments and create designs with binary operations or specific methods on'
                   ' Factors and groups of Factors',
    'author': 'Joshua McCrary',
    'url': '',
    'download_url': '',
    'author_email': 'jmccrary@spa.com',
    'version': '0.8.0',
    'install_requires': ['numpy'],
    'packages': [],
    'scripts': [],
    'name': 'experimentspydesign'
    }
    
setup(**config)
