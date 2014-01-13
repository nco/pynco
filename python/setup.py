#!/usr/bin/env python
from setuptools import setup

setup (name = 'nco',
  version = '0.0beta',
  author = "Joe Hamman",
  author_email= "jhamman@hydro.washington.edu",
  license = "GPLv2",
  description = """python bindings to NCO""",
  py_modules = ["nco"],
  url = "",
  classifiers = [
        "Development Status :: 2 - Pre-Alpha",
        "Topic :: Utilities",
        "Operating System :: POSIX",
        "Programming Language :: Python",
    ],
  )