
import os
# import tempfile
# import sys
# import glob
from stat import *
from nco import *
import numpy as np
# import pylab as pl
import netCDF4
import scipy
import pytest


ops = ['ncap2', 'ncatted', 'ncbo', 'nces', 'ncecat', 'ncflint', 'ncks',
       'ncpdq', 'ncra', 'ncrcat', 'ncrename', 'ncwa', 'ncdump']


def rm(files):
    for f in files:
        if os.path.exists(f):
            os.system("rm "+f)


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
    #print "\n".join(operators)


@pytest.mark.usefixtures("foo_nc", "bar_nc")
def test_use_list_inputs(foo_nc, bar_nc):
    nco = Nco(debug=True)
    infiles = [foo_nc, bar_nc]
    nco.ncrcat(input=infiles, output='out.nc')


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


@pytest.mark.usefixtures("foo_nc", "bar_nc")
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
    assert hasattr(nco, 'nonExistingMethod') == False
    try:
        nco.ncks(input="", output="")
    except NCOException:
        pass


@pytest.mark.usefixtures("foo_nc")
def test_returnArray(foo_nc):
    nco = Nco()
    random1 = nco.ncea(input=foo_nc, returnCdf=True).variables['random'][:]
    assert type(random1) == np.ndarray
    random2 = nco.ncea(input=foo_nc, returnArray='random')
    assert type(random2) == np.ndarray
    np.testing.assert_equal(random1, random2)


@pytest.mark.usefixtures("bar_mask_nc")
def test_returnMaArray(bar_mask_nc, random_masked_field):
    nco = Nco()
    field = nco.ncea(input=bar_mask_nc, returnMaArray='random')
    assert type(field) == np.ma.core.MaskedArray


def test_returnCdf(foo_nc):
    nco = Nco(cdfMod='scipy')
    testCdf = nco.ncea(input=foo_nc, returnCdf=True)
    assert type(testCdf) == scipy.io.netcdf.netcdf_file
    expected_vars = ['time', 'random']
    for var in expected_vars:
        assert var in list(testCdf.variables.keys())

    nco = Nco(cdfMod='netcdf4')
    testCdf = nco.ncea(input=foo_nc, returnCdf=True)
    assert type(testCdf) == netCDF4.Dataset
    for var in expected_vars:
        assert var in list(testCdf.variables.keys())


def test_cdf_mod_scipy():
    nco = Nco()
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
    assert nco.forceOutput == False
    nco = Nco(returnCdf=True,
              returnNoneOnError=True)
    assert nco.returnCdf
    assert nco.returnNoneOnError


@pytest.mark.usefixtures("bar_nc")
def test_operatorPrintsOut(bar_nc):
    nco = Nco()
    dump = nco.ncdump(input=bar_nc, options='-h')
    print(dump)
