"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
import codecs
import os
import re

here = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file
with codecs.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

def read(*parts):
    with codecs.open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()

def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

setup(
    name='SubregSimulator',
    version=find_version("subregsim", "__main__.py"),
    description='Simple Subreg.cz API simulator',
    long_description=long_description,
    long_description_content_type='text/markdown',

    url='https://github.com/oldium/subregsim',

    author='Oldřich Jedlička',
    author_email='oldium.pro@gmail.com',

    # See https://pypi.org/classifiers/
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'Topic :: Utilities',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],

    keywords='subreg api simulator',

    packages=find_packages(exclude=['contrib', 'config', 'docs', 'tests']),

    # See https://packaging.python.org/en/latest/requirements.html
    install_requires=['future',
                      'configargparse'],
    extras_require={
        'pysimplesoap': ['PySimpleSOAP'],
        'spyne': ['spyne'],
        'dns': ['dnslib'],
        },

    entry_points={
        'console_scripts': [
            'subregsim=subregsim.__main__:main',
        ],
    },

    project_urls={
        'Bug Reports': 'https://github.com/oldium/subregsim/issues',
        'Say Thanks!': 'https://saythanks.io/to/oldium',
        'Source': 'https://github.com/oldium/subregsim/',
    },
)
