"""
Unit tests for nco.py.
"""
import distutils.spawn
import os
import subprocess

import netCDF4
import numpy as np
import pytest
import scipy.io.netcdf

from nco import Nco, NCOException
from nco.custom import Atted, Limit, LimitSingle, Rename

ops = [
    "ncap2",
    "ncatted",
    "ncbo",
    "nces",
    "ncecat",
    "ncflint",
    "ncks",
    "ncpdq",
    "ncra",
    "ncrcat",
    "ncrename",
    "ncwa",
]


pytestmark = pytest.mark.usefixtures("cleandir")


def test_nco_present():
    ncopath = distutils.spawn.find_executable("ncks")
    # ncopath = which('ncks')
    assert os.path.isfile(ncopath)


def test_debug():
    nco = Nco()
    assert nco.debug == 0
    nco = Nco(debug=True)
    assert nco.debug
    nco.debug = False


def test_ops():
    nco = Nco()
    for op in ops:
        assert op in nco.operators


def test_mod_version():
    nco = Nco()
    assert "0.0.0" == nco.module_version


def test_get_operators():
    nco = Nco()
    for op in ops:
        assert op in dir(nco)


def test_list_all_operators():
    nco = Nco()
    operators = nco.operators
    operators.sort()


@pytest.mark.usefixtures("foo_nc", "bar_nc")
def test_use_list_inputs(foo_nc, bar_nc):
    nco = Nco(debug=True)
    infiles = [foo_nc, bar_nc]
    nco.ncrcat(input=infiles, output="out.nc")


@pytest.mark.usefixtures("foo_nc")
def test_use_list_options(foo_nc):
    nco = Nco(debug=True)
    options = []
    options.extend(["-a 'units,time,o,c,days since 1999-01-01'"])
    options.extend(["-a", "long_name,time,o,c,time"])
    options.extend(["-a", "calendar,time,o,c,noleap"])
    nco.ncatted(input=foo_nc, output="out.nc", options=options)


@pytest.mark.usefixtures("foo_nc", "bar_nc")
def test_ncra_mult_files(foo_nc, bar_nc):
    nco = Nco(debug=True)
    infiles = [foo_nc, bar_nc]
    nco.ncra(input=infiles, output="out.nc")


@pytest.mark.usefixtures("foo_nc")
def test_ncra_single_file(foo_nc):
    nco = Nco(debug=True)
    infile = foo_nc
    nco.ncra(input=infile, output="out.nc")


@pytest.mark.usefixtures("foo_nc")
def test_ncks_extract(foo_nc):
    nco = Nco(debug=True)
    infile = foo_nc
    nco.ncks(input=infile, output="out.nc", variable="random")


@pytest.mark.usefixtures("foo_nc", "bar_nc")
def test_ncea_mult_files(foo_nc, bar_nc):
    nco = Nco(debug=True)
    infiles = [foo_nc, bar_nc]
    nco.ncea(input=infiles, output="out.nc")


def test_overwrite_existing_file(foo_nc, tmp_path, monkeypatch):
    """
    By default the nco tools will prompt the user before overwriting a file.
    The output of all commands is collected by pynco
    so the user will never see the prompt.
    This can result in `nco.ncatted` etc hanging indefinitely waiting for input
    that will never come.
    """
    outfile = str(tmp_path / 'out.nc')
    with open(outfile, 'w') as f:
        f.write('boop')

    # Monkeypatch `Popen.communicate` to have a default timeout value
    # so that a failed test here doesn't cause the test suite to hang.
    class PopenTimeout(subprocess.Popen):
        def communicate(self, *args, timeout=2, **kwargs):
            return super().communicate(*args, timeout=timeout, **kwargs)

    monkeypatch.setattr(subprocess, 'Popen', PopenTimeout)

    # Disable forced overwriting of files to expose this potential issue.
    # This method is one of many.
    nco = Nco(debug=True, force_output=False)
    with pytest.raises(NCOException):
        # This should fail with an NCOException because the tool aborted when
        # it did not get user input.
        # The test fails if a subprocess.TimeoutExpired exception is raised.
        nco.ncatted(input=foo_nc, output=outfile, options=[
            '-a', 'att_name,time,o,c,value',
        ])


def test_error_exception():
    nco = Nco()
    assert hasattr(nco, "nonExistingMethod") is False
    with pytest.raises(NCOException):
        nco.ncks(input="", output="")


@pytest.mark.usefixtures("foo_nc")
def test_return_array(foo_nc):
    nco = Nco(cdf_module="netcdf4")
    random1 = nco.ncea(
        input=foo_nc, output="tmp.nc", returnCdf=True, options=["-O"]
    ).variables["random"][:]
    assert isinstance(random1, np.ndarray)
    random2 = nco.ncea(
        input=foo_nc, output="tmp.nc", returnArray="random", options=["-O"]
    )
    assert isinstance(random2, np.ndarray)
    np.testing.assert_equal(random1, random2)


@pytest.mark.usefixtures("bar_mask_nc", "random_masked_field")
def test_return_ma_array(bar_mask_nc, random_masked_field):
    nco = Nco()
    field = nco.ncea(
        input=bar_mask_nc, output="tmp.nc", returnMaArray="random", options=["-O"]
    )
    assert type(field) == np.ma.core.MaskedArray


@pytest.mark.usefixtures("foo_nc")
def test_return_cdf(foo_nc):
    nco = Nco(cdf_module="scipy")
    test_cdf = nco.ncea(input=foo_nc, output="tmp.nc", returnCdf=True, options=["-O"])
    assert type(test_cdf) == scipy.io.netcdf.netcdf_file
    expected_vars = ["time", "random"]
    for var in expected_vars:
        assert var in list(test_cdf.variables.keys())

    nco = Nco(cdf_module="netcdf4")
    test_cdf = nco.ncea(input=foo_nc, output="tmp.nc", returnCdf=True, options=["-O"])
    assert type(test_cdf) == netCDF4.Dataset
    for var in expected_vars:
        assert var in list(test_cdf.variables.keys())


@pytest.fixture(scope="module")
def test_atted():
    atted_list = [
        Atted(
            mode="overwrite", att_name="units", var_name="temperature", value="Kelvin"
        ),
        Atted(
            mode="overwrite",
            att_name="min",
            var_name="temperature",
            value=-127,
            stype="byte",
        ),
        Atted(
            mode="overwrite",
            att_name="max",
            var_name="temperature",
            value=127,
            stype="int16",
        ),
        Atted(
            mode="modify",
            att_name="min-max",
            var_name="pressure",
            value=[100, 10000],
            stype="int32",
        ),
        Atted(
            mode="create",
            att_name="array",
            var_name="time_bands",
            value=range(1, 10, 2),
            stype="d",
        ),
        Atted(
            mode="append", att_name="mean", var_name="time_bands", value=3.14159826253
        ),  # default to double
        Atted(
            mode="append",
            att_name="mean_float",
            var_name="time_bands",
            value=3.14159826253,
            stype="float",
        ),
        # d convert type to float
        Atted(
            mode="append",
            att_name="mean_sng",
            var_name="time_bands",
            value=3.14159826253,
            stype="char",
        ),
        Atted(
            mode="nappend",
            att_name="units",
            var_name="height",
            value="height in mm",
            stype="string",
        ),
        Atted(
            mode="create",
            att_name="long_name",
            var_name="height",
            value="height in feet",
        ),
        Atted(
            mode="nappend",
            att_name="units",
            var_name="blob",
            value=[1000000.0, 2.0],
            stype="d",
        ),
    ]

    # regular function args
    atted_list += [
        Atted(
            "append",
            "long_name",
            "temperature",
            ("mean", "sea", "level", "temperature"),
        ),
        Atted("delete", "short_name", "temp"),
        Atted("delete", "long_name", "relative_humidity"),
    ]

    ar = ("mean", "sea", "level", "temperature", 3.1459, 2.0)
    val = np.dtype(np.complex).type(123456.0)
    val2 = np.dtype(np.bool).type(False)

    # val=10.0

    atted_list += [
        Atted("append", "long_name", "temperature", ar),
        Atted(mode="delete", att_name=".*"),
        Atted(mode="append", att_name="array", var_name="time", value=val, stype="ll"),
        Atted(mode="append", att_name="bool", var_name="time", value=val2, stype="b"),
        Atted("nappend", "long", "random", 2 ** 33, stype="ull"),
    ]

    for atted in atted_list:
        print(atted.prn_option())

    limit_list = [
        Limit("lat", 0.0, 88.1),
        Limit("time", 0, 10, 3),
        Limit("time", 1.0, 2e9, 3),
        Limit(dmn_name="three", srt=10, end=30, srd=4, drn=2),
        Limit(dmn_name="three", srd=4),
        Limit(dmn_name="three", drn=3),
        LimitSingle("three", 20.0),
    ]

    for limit in limit_list:
        print(limit.prn_option())

    renames = dict(
        {"lon": "longitude", "lat": "latitude", "lev": "level", "dog": "cat"}
    )
    rename = Rename("g", renames)
    print(rename.prn_option())


@pytest.mark.usefixtures("foo_nc")
def test_ncatted_with_atted(foo_nc, tmp_path):
    """
    Test that ncatted works with names and values containing special
    characters.
    """
    nco = Nco(debug=True)

    output = str(tmp_path / 'out.nc')
    nco.ncatted(input=foo_nc, output=output, options=[
        Atted(
            mode='create', var_name='random', att_name='attr',
            value="some value with spaces"
        ),
        Atted(
            mode='create', var_name='random', att_name='tricky "name"!',
            value="the name is tricky here!"
        ),
        Atted(mode='delete', var_name='time', att_name='units'),
        Atted(
            mode='create', var_name='global', att_name='1 2 3',
            value="one two three"
        ),
    ])

    # Check that the attributes were added to the `random` variable
    ds = netCDF4.Dataset(output)
    random_variable = ds.variables['random']
    assert random_variable.getncattr('attr') == 'some value with spaces'
    assert random_variable.getncattr('tricky "name"!') == 'the name is tricky here!'

    # Check that the `units` attribute on the `time` variable was removed
    time_variable = ds.variables['time']
    assert time_variable.ncattrs() == []

    # Check that the dataset attribute was added
    assert ds.getncattr('1 2 3') == 'one two three'


def test_cdf_mod_scipy():
    nco = Nco(cdf_module="scipy")
    nco.set_return_array()
    print(("nco.cdf_module: {0}".format(nco.cdf_module)))
    assert nco.cdf_module == "scipy"


def test_cdf_mod_netcdf4():
    nco = Nco(cdf_module="netcdf4")
    nco.set_return_array()
    print(("nco.cdf_module: {0}".format(nco.cdf_module)))
    assert nco.cdf_module == "netcdf4"


def test_init_options():
    nco = Nco(debug=True)
    assert nco.debug
    nco = Nco(force_output=False)
    assert nco.force_output is False
    nco = Nco(returnCdf=True, return_none_on_error=True)
    assert nco.return_cdf
    assert nco.return_none_on_error


@pytest.mark.usefixtures("bar_nc")
def test_operator_prints_out(bar_nc):
    nco = Nco()
    dump = nco.ncks(input=bar_nc, options=["--help"])
    print(dump)
