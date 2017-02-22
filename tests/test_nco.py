#!/usr/bin/env python
"""
Unit tests for nco.py.

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
import os
import sys
from nco import NCOException, Nco, which
import numpy as np
import netCDF4
import scipy
import pytest
from custom import Atted,Limit,LimitSingle,Rename



ops = ['ncap2', 'ncatted', 'ncbo', 'nces', 'ncecat', 'ncflint', 'ncks',
       'ncpdq', 'ncra', 'ncrcat', 'ncrename', 'ncwa', 'ncdump']


def rm(files):
    for f in files:
        if os.path.exists(f):
            os.system("rm " + f)


def test_nco_present():
    ncopath = which('ncks')
    assert os.path.isfile(ncopath)


def testDbg():
    nco = Nco()
    assert nco.debug == 0
    nco = Nco(debug=True)
    assert nco.debug
    nco.debug = False


def testOps():
    nco = Nco()
    for op in ops:
        assert op in nco.operators


def test_mod_version():
    nco = Nco()
    assert '0.0.0' == nco.module_version()


def test_getOperators():
    nco = Nco()
    for op in ops:
        assert op in dir(nco)


def test_listAllOperators():
    nco = Nco()
    operators = nco.operators
    operators.sort()


@pytest.mark.usefixtures("foo_nc", "bar_nc")
def test_use_list_inputs(foo_nc, bar_nc):
    nco = Nco(debug=True)
    infiles = [foo_nc, bar_nc]
    nco.ncrcat(input=infiles, output='out.nc')


@pytest.mark.usefixtures("foo_nc")
def test_use_list_options(foo_nc):
    nco = Nco(debug=True)
    options = []
    options.extend(['-a', 'units,time,o,c,days since 1999-01-01'])
    options.extend(['-a', 'long_name,time,o,c,time'])
    options.extend(['-a', 'calendar,time,o,c,noleap'])
    nco.ncrcat(input=foo_nc, output='out.nc', options=options)


@pytest.mark.usefixtures("foo_nc", "bar_nc")
def test_ncra_mult_files(foo_nc, bar_nc):
    nco = Nco(debug=True)
    infiles = [foo_nc, bar_nc]
    nco.ncra(input=infiles, output='out.nc')


@pytest.mark.usefixtures("foo_nc")
def test_ncra_single_file(foo_nc):
    nco = Nco(debug=True)
    infile = foo_nc
    nco.ncra(input=infile, output='out.nc')


@pytest.mark.usefixtures("foo_nc")
def test_ncks_extract(foo_nc):
    nco = Nco(debug=True)
    infile = foo_nc
    nco.ncks(input=infile, output='out.nc', variable='random')


@pytest.mark.usefixtures("foo_nc", "bar_nc")
def test_ncea_mult_files(foo_nc, bar_nc):
    nco = Nco(debug=True)
    infiles = [foo_nc, bar_nc]
    nco.ncea(input=infiles, output='out.nc')


def test_errorException():
    nco = Nco()
    assert hasattr(nco, 'nonExistingMethod') is False
    with pytest.raises(NCOException):
        nco.ncks(input="", output="")


@pytest.mark.usefixtures("foo_nc")
def test_returnArray(foo_nc):
    nco = Nco(cdfMod='netcdf4')
    random1 = nco.ncea(input=foo_nc, output="tmp.nc", returnCdf=True, options=['-O']).variables['random'][:]
    assert type(random1) == np.ndarray
    random2 = nco.ncea(input=foo_nc, output="tmp.nc",returnArray='random' ,options=['-O'])
    assert type(random2) == np.ndarray
    np.testing.assert_equal(random1, random2)


@pytest.mark.usefixtures("bar_mask_nc", "random_masked_field")
def test_returnMaArray(bar_mask_nc, random_masked_field):
    nco = Nco()
    field = nco.ncea(input=bar_mask_nc, output="tmp.nc", returnMaArray='random', options=['-O'])
    assert type(field) == np.ma.core.MaskedArray


@pytest.mark.usefixtures("foo_nc")
def test_returnCdf(foo_nc):
    nco = Nco(cdfMod='scipy')
    testCdf = nco.ncea(input=foo_nc, output="tmp.nc", returnCdf=True,options=['-O'])
    assert type(testCdf) == scipy.io.netcdf.netcdf_file
    expected_vars = ['time', 'random']
    for var in expected_vars:
        assert var in list(testCdf.variables.keys())

    nco = Nco(cdfMod='netcdf4')
    testCdf = nco.ncea(input=foo_nc, output="tmp.nc", returnCdf=True, options=['-O'])
    assert type(testCdf) == netCDF4.Dataset
    for var in expected_vars:
        assert var in list(testCdf.variables.keys())

@pytest.fixture(scope="module")
def test_atted():
    AttedList = [
        Atted(mode="overwrite", att_name="units", var_name="temperature", value="Kelvin"),
        Atted(mode="overwrite", att_name="min", var_name="temperature", value=-127, stype='byte'),
        Atted(mode="overwrite", att_name="max", var_name="temperature", value=127, stype='int16'),
        Atted(mode="modify", att_name="min-max", var_name="pressure", value=[100, 10000], stype='int32'),
        Atted(mode="create", att_name="array", var_name="time_bands", value=range(1, 10, 2), stype='d'),
        Atted(mode="append", att_name="mean", var_name="time_bands", value=3.14159826253),  # default to double
        Atted(mode="append", att_name="mean_float", var_name="time_bands", value=3.14159826253, stype='float'),
        # d convert type to float
        Atted(mode="append", att_name="mean_sng", var_name="time_bands", value=3.14159826253, stype='char'),
        Atted(mode="nappend", att_name="units", var_name="height", value="height in mm", stype='string'),
        Atted(mode="create", att_name="long_name", var_name="height", value="height in feet"),
        Atted(mode="nappend", att_name="units", var_name="blob", value=[1000000., 2.], stype='d')
    ]

    # regular function args
    AttedList += [
        Atted("append", "long_name", "temperature", ("mean", "sea", "level", "temperature")),
        Atted("delete", "short_name", "temp"),
        Atted("delete", "long_name", "relative_humidity")
    ]

    ar = ("mean", "sea", "level", "temperature", 3.1459, 2.0)
    val = np.dtype(np.complex).type(123456.0)
    val2 = np.dtype(np.bool).type(False)

    # val=10.0

    AttedList += [
        Atted("append", "long_name", "temperature", ar),
        Atted(mode="delete", att_name=".*"),
        Atted(mode="append", att_name="array", var_name="time", value=val, stype='ll'),
        Atted(mode="append", att_name="bool", var_name="time", value=val2, stype='b'),
        Atted("nappend", "long", "random", 2 ** 33, stype='ull')
    ]

    for a in AttedList:
        print(a.prn_option())

    LimitList = [Limit("lat", 0.0, 88.1),
                 Limit("time", 0, 10, 3),
                 Limit("time", 1.0, 2e9, 3),
                 Limit(dmn_name="three", srt=10, end=30, srd=4, drn=2),
                 Limit(dmn_name="three", srd=4),
                 Limit(dmn_name="three", drn=3),
                 LimitSingle("three", 20.0)
                 ]

    for l in LimitList:
        print(l.prn_option())

    tstrename = dict({'lon': 'longitude', 'lat': 'latitude', 'lev': 'level', 'dog': 'cat'})
    myrename = Rename("g", tstrename)
    print(myrename.prn_option())

def test_cdf_mod_scipy():
    nco = Nco(cdfMod='scipy')
    nco.setReturnArray()
    print(('nco.cdfMod: {0}'.format(nco.cdfMod)))
    assert nco.cdfMod == "scipy"


def test_cdf_mod_netcdf4():
    nco = Nco(cdfMod='netcdf4')
    nco.setReturnArray()
    print(('nco.cdfMod: {0}'.format(nco.cdfMod)))
    assert nco.cdfMod == "netcdf4"


def test_initOptions():
    nco = Nco(debug=True)
    assert nco.debug
    nco = Nco(forceOutput=False)
    assert nco.forceOutput is False
    nco = Nco(returnCdf=True,
              returnNoneOnError=True)
    assert nco.returnCdf
    assert nco.returnNoneOnError


@pytest.mark.usefixtures("bar_nc")
def test_operatorPrintsOut(bar_nc):
    nco = Nco()
    dump = nco.ncdump(input=bar_nc, options=['-h'])
    print(dump)
