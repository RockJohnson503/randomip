# encoding: utf-8

"""
File: setup.py
Author: Rock Johnson
"""
import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst'), encoding='utf-8') as readme:
    README = readme.read()

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='randomip',
    version='1.1',
    packages=find_packages(),
    include_package_data=True,
    license='BSD License',
    description='一个小型的随机ip代理池.',
    long_description=README,
    url='https://www.example.com/',
    author='Rock Johnson',
    author_email='rockjohnson270@gamil.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Twisted',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    install_requires=[
        'Twisted',
        'scrapy>=1.6.0',
        'requests>=2.22.0',
        'txrequests>=0.9.6',
    ]
)