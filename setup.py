
from setuptools import setup, find_packages

import sys
sys.path.append("./pluralkit")
from __version__ import __version__

# Thanks to Mark Smith (@Judy2k)'s very helpful talk about PyPI
# https://youtu.be/GIF3LaRqgXo?t=297

with open("README.md", "r", encoding="utf-8") as fh:
   long_description = fh.read()

setup(
   name="pluralkit",
   version=__version__,
   description="Python wrapper for PluralKit's API.",
   license="MIT",
   packages=find_packages(),
   classifiers=[ # https://pypi.org/classifiers/
      "Development Status :: 3 - Alpha",
      "Programming Language :: Python :: 3.6", # f-strings
      "Programming Language :: Python :: 3.7",
      "Programming Language :: Python :: 3.8",
      "Programming Language :: Python :: 3.9",
      "License :: OSI Approved :: MIT License",
      "Operating System :: OS Independent",
      "Intended Audience :: Developers",
      "Natural Language :: English",
      "Topic :: Internet",
      "Topic :: Software Development :: Libraries",
      "Topic :: Software Development :: Libraries :: Python Modules",
      "Topic :: Utilities",
   ],
   long_description=long_description,
   long_description_content_type="text/markdown",
   install_requires=[
      "httpx>=0.23.0", # https://www.python-httpx.org/
      "colour>=0.1",
      "pytz>=2021",
   ],
   extras_require = {
      "dev": [
         "Sphinx==5.0.1", # documentation!
         "sphinx-autodoc-typehints", # better sphinx parsing
         "sphinx-book-theme", # Book theme
         "sphinxcontrib-trio", # better async handling
         "mypy", # type checking
         "types-pytz==2021.1.0", # type checking with pytz
         "pytest", # testing module
         "check-manifest", # creating MANIFEST.in
         "twine", # for uploading to PyPI
         "wheel>=0.36.2", # for building wheels
         "jinja2<3.1.0", # RDT bug #9037 (still not fixed)
      ]
   },
   python_requires=">=3.6.0",
   url="https://github.com/almonds0166/pluralkit.py",
   author="Madison Landry, Alyx Warner",
   author_email="pkpy@mit.edu",
   project_urls={
     "Documentation": "https://pluralkit.readthedocs.io/en/latest/",
     "Issue tracker": "https://github.com/almonds0166/pluralkit.py/issues",
   },
)