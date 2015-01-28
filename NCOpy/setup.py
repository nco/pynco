"""
setup.py

License:
    Python Bindings for NCO (NetCDF Operators)
    Copyright (C) 2015  Joe Hamman

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

from setuptools import setup

setup(name='nco',
      version='0.0.2',
      author="Joe Hamman",
      author_email="jhamman@hydro.washington.edu",
      license="GPLv2",
      description="""python bindings to NCO""",
      py_modules=["nco"],
      url="https://raw2.github.com/jhamman/nco-bindings/",
      download_url="https://raw2.github.com/jhamman/nco-bindings/tarball/0.0.2",
      keywords=['netcdf', 'climate'],
      classifiers=["Development Status :: 2 - Pre-Alpha",
                   "Topic :: Utilities",
                   "Operating System :: POSIX",
                   "Programming Language :: Python",
                   ],
      )
