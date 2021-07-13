
from setuptools import setup, find_packages

from pluralkit import __version__

# Thanks to Mark Smith (@Judy2k)'s very helpful talk about PyPI
# https://youtu.be/GIF3LaRqgXo?t=297

with open("README.md", "r") as fh:
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
      "httpx==0.18.2", # https://www.python-httpx.org/
      "colour>=0.1",
      "pytz>=2021",
   ],
   extras_require = {
      "dev": [
         "Sphinx==3.5.4", # documentation!
         "sphinx-autodoc-typehints==1.12.0", # better sphinx parsing
         "sphinx-book-theme==0.1.0", # Book theme
         "sphinxcontrib-trio==1.1.2", # better async handling
         "mypy==0.910", # type checking
         "types-pytz==2021.1.0", # type checking with pytz
         "pytest==6.2.4", # testing module
         "check-manifest==0.46", # creating MANIFEST.in
         "twine==3.4.1", # for uploading to PyPI
         "wheel>=0.36.2", # for building wheels
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