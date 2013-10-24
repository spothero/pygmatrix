
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'PyGMatrix',
    'author': 'SpotHero',
    'url': '',
    'download_url': '',
    'author_email': 'cezar@spothero.com',
    'version': '0.1',
    'install_requires': ['nose', 'requests<2', 'anyjson'],
    'packages': ['pygmatrix'],
    'scripts': [],
    'name': 'pygmatrix'
}

setup(**config)
