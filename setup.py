# Project WireGen

# Python Modules
from setuptools import setup, find_packages

# Local Modules
from wiregen.version import VERSION

DESCRIPTION = 'Wireguard Config Generator',
# LONG_DESCRIPTION = DESCRIPTION

# with open('README.md', 'r', encoding='utf-8') as readme:
#     LONG_DESCRIPTION = readme.read()

setup(
    name='wiregen',
    author='Michael Buckley',
    description=DESCRIPTION,
    # long_description=LONG_DESCRIPTION,
    # long_description_content_type = 'text/markdown',
    version=VERSION,
    packages=find_packages(),
    keywords=['wireguard']
)