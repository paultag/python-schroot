from schroot import __appname__, __version__
from setuptools import setup


long_description = ""

setup(
    name=__appname__,
    version=__version__,
    scripts=[],
    packages=[
        'schroot',
    ],
    author="Paul Tagliamonte",
    author_email="tag@pault.ag",
    long_description=long_description,
    description='schroot chroot schroots!',
    license="Expat",
    url="http://pault.ag/",
    platforms=['any'],
)
