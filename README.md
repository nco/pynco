nco-bindings
============

Language bindings for NCO.  A fork from Ralf Mueller's [cdo-bindings](https://github.com/Try2Code/cdo-bindings).

## nco.py - Use Python to access the power of NCO

This package contains the module NCO, which implements a python style access to
the NetCDF Operators NCO. NCO is a command line tool for processing
netCDF data. Its main focus if climate data, but it can by used for other
purposes too.

## Installation

### Python Installation

   `./setup.py install`

Coming Soon: Download and install nco.py via pypi:

  `pip install cdo`

### Requirements

nco.py requires working NCO binaries, but has does not have special python version requirements. For returning multi-dimensional arrays (numpy addtional netcdf-io modules are needed. These are [scipy](http://docs.scipy.org/doc/scipy/reference/generated/scipy.io.netcdf.netcdf_file.html) or [netCDF-4](https://code.google.com/p/netcdf4-python/).

## Usage

### Run operators

For python an instance has to be created first

   `nco = Nco()`

* File information

    `ncdump_string = nco.ncdump(input=ifile)`

* Operators with user defined regular output files

    `nco.timmin(input=ifile, output=ofile)`

* Use temporary output files

    `tminFile = nco.ncrcat(input=ifile)`

* Set global NCO options

   `nco.ncks(input=ifile, output=ofile, options="--netcdf4")`

* Return multi-dimension arrrays

   `temperatures = nco.ncra(input=ifile,:returnArray=True).variables['T'][:]`
   `temperatures = nco.ncra(input=ifile,:returnCdf=True).variables['T'][:]`
   `temperatures = nco.ncra(input=ifile,:returnArray='T')`

## Tempfile helpers

nco.py includes a simple tempfile wrapper, which make live easier, when writing your own scripts

## Support, Issues, Bugs, ...

Please use the github page for this code: https://github.com/jhamman/nco-bindings

## Changelog
* next:
   - add ncdump --> python dictionary function

## License

nco.py makes use of the GPLv2 License, see COPYING

---

## Other stuff

* Author: Joe Hamman <jhamman@hydro.washington.edu>
* Requires: NCO version 4.x.x or newer
* License:  Copyright 2013 by Joe Hamman.  Released under GPLv2 license.  See the COPYING file included in the distribution.
