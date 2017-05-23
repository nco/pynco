
# content of conftest.py
import os
import pytest
import tempfile
import numpy as np
import netCDF4
import datetime
from dateutil import relativedelta

stdtimeunits = 'days since 1990-01-01'
noleapcalendar = 'noleap'
monthlydatestrformat = 'Foo.bar.ha.%Y-%m.nc'


@pytest.fixture(scope="module")
def cleandir():
    newpath = tempfile.mkdtemp()
    os.chdir(newpath)


@pytest.fixture(scope="module")
def tempdestdir():
    return tempfile.mkdtemp()


@pytest.fixture(scope="module")
def tempsrcdir():
    return tempfile.mkdtemp()


@pytest.fixture(scope="module")
def random_field():
    return np.random.rand(5, 5)


@pytest.fixture(scope="module")
def mask4tests():
    return np.random.random_integers(0, 1, (1, 5, 5))


@pytest.fixture(scope="module")
def random_masked_field(mask4tests):
    field = np.ma.masked_array(np.random.rand(1, 5, 5))
    field.mask = mask4tests
    return field


@pytest.fixture(scope="module")
def hdf_file(random_field, tempsrcdir):
    try:
        import h5py
        filename = os.path.join(tempsrcdir, 'testhdf.hdf5')
        f = h5py.File(filename, 'w')
        shape = random_field.shape
        dset = f.create_dataset("random_field", shape, dtype='f')
        dset[:, :] = random_field
        f.close()
        return filename
    except (ImportError, AttributeError):
        return None


@pytest.fixture(scope="module")
def foo_nc(random_field):
    """ a simple netCDF file with a random field"""
    tempdir = tempsrcdir()
    filename = os.path.join(tempdir, 'foo.nc')
    f = netCDF4.Dataset(filename, 'w', format='NETCDF3_CLASSIC')
    shape = random_field.shape
    f.createDimension('dim0', shape[0])
    f.createDimension('dim1', shape[1])
    time = f.createDimension('time', None)
    var = f.createVariable('random', 'f8', ('time', 'dim0', 'dim1',))
    time = f.createVariable('time', 'f8', ('time'))
    time.units = stdtimeunits
    var[0, :, :] = random_field
    time[:] = 1.0
    f.close()
    return filename


@pytest.fixture(scope="module")
def bar_nc(random_field):
    """ a simple netCDF file with a random field * 2"""
    tempdir = tempsrcdir()
    filename = os.path.join(tempdir, 'bar.nc')
    f = netCDF4.Dataset(filename, 'w')
    shape = random_field.shape
    f.createDimension('dim0', shape[0])
    f.createDimension('dim1', shape[1])
    time = f.createDimension('time', None)
    var = f.createVariable('random', 'f8', ('time', 'dim0', 'dim1',))
    time = f.createVariable('time', 'f8', ('time'))
    time.units = stdtimeunits
    var[0, :, :] = random_field*2.0
    time[:] = 2.0
    f.close()
    return filename


@pytest.fixture(scope="module")
def bar_mask_nc(random_masked_field):
    """ a simple netCDF file with a random field * 2"""
    tempdir = tempsrcdir()
    filename = os.path.join(tempdir, 'bar.nc')
    f = netCDF4.Dataset(filename, 'w', format='NETCDF3_CLASSIC')

    shape = random_masked_field.shape
    f.createDimension('dim0', shape[1])
    f.createDimension('dim1', shape[2])
    time = f.createDimension('time', 1)
    var = f.createVariable('random', 'f8', ('time', 'dim0', 'dim1',))
    time = f.createVariable('time', 'f8', ('time'))
    time.units = stdtimeunits
    var[:, :, :] = random_masked_field*2.0
    time[:] = 2.0
    f.close()
    return filename


@pytest.fixture(scope="module")
def monthly_filelist(random_field, monthlydatetimelist, tempsrcdir):
    """Create a bunch of sample monthly netcdf files with real times"""
    filelist = []
    tempdir = tempsrcdir()
    for date in monthlydatetimelist:
        filename = date.strftime(monthlydatestrformat)
        filename = os.path.join(tempdir, filename)
        f = netCDF4.Dataset(filename, 'w')
        shape = random_field.shape
        f.createDimension('dim0', shape[0])
        f.createDimension('dim1', shape[1])
        time = f.createDimension('time', 1)
        var = f.createVariable('random', 'f8', ('time', 'dim0', 'dim1',))
        time = f.createVariable('time', 'f8', ('time'))
        time.units = stdtimeunits
        time.calendar = noleapcalendar
        var[:, :, :] = random_field
        time[:] = netCDF4.date2num(date, stdtimeunits,
                                   calendar=noleapcalendar)
        f.close()

        filelist.append(filename)
    return filelist


@pytest.fixture(scope="module")
def testfiles8589(random_field, tempsrcdir):
    """Create a bunch of sample monthly netcdf files with real times"""
    filelist = []
    for year in range(1985, 1990):
        date = datetime.datetime(year, 1, 1)
        filename = date.strftime("%y.nc")
        filename = os.path.join(tempsrcdir, filename)
        f = netCDF4.Dataset(filename, 'w')
        shape = random_field.shape
        f.createDimension('dim0', shape[0])
        f.createDimension('dim1', shape[1])
        time = f.createDimension('time', 1)
        var = f.createVariable('random', 'f8', ('time', 'dim0', 'dim1',))
        time = f.createVariable('time', 'f8', ('time'))
        time.units = stdtimeunits
        time.calendar = noleapcalendar
        var[:, :, :] = random_field
        time[:] = netCDF4.date2num(date, stdtimeunits,
                                   calendar=noleapcalendar)
        f.close()

        filelist.append(filename)
    return filelist


@pytest.fixture(scope="module")
def testfile85(random_field, tempsrcdir):
    """Create a bunch of sample monthly netcdf files with real times"""
    dates = [datetime.datetime(1985, 1, 1) + datetime.timedelta(days=d) for
             d in range(0, 365)]
    tempdir = tempsrcdir()
    filename = os.path.join(tempdir, "85.nc")
    f = netCDF4.Dataset(filename, 'w')
    shape = random_field.shape
    f.createDimension('dim0', shape[0])
    f.createDimension('dim1', shape[1])
    time = f.createDimension('time', len(dates))
    var = f.createVariable('random', 'f8', ('time', 'dim0', 'dim1',))
    time = f.createVariable('time', 'f8', ('time'))
    time.units = stdtimeunits
    time.calendar = noleapcalendar
    var[:, :, :] = random_field
    time[:] = netCDF4.date2num(dates, stdtimeunits, calendar=noleapcalendar)
    f.close()
    return filename


@pytest.fixture(scope="module")
def testfileglobal(tempsrcdir):
    """Create a bunch of sample monthly netcdf files with real times"""
    dates = [datetime.datetime.now()]
    # tempdir = tempsrcdir()
    filename = os.path.join(tempsrcdir, "global.nc")
    f = netCDF4.Dataset(filename, 'w')
    random_field = np.random.rand(1, 180, 360)  # 1degree resolution
    shape = random_field.shape
    f.createDimension('lat', shape[1])
    f.createDimension('lon', shape[2])
    time = f.createDimension('time', len(dates))
    var = f.createVariable('random', 'f8', ('time', 'lat', 'lon',))
    lon = f.createVariable('lon', 'f8', ('lon',))
    lat = f.createVariable('lat', 'f8', ('lat',))
    time = f.createVariable('time', 'f8', ('time'))
    time.units = stdtimeunits
    time.calendar = noleapcalendar
    var[:, :, :] = random_field
    time[:] = netCDF4.date2num(dates, stdtimeunits, calendar=noleapcalendar)
    lat[:] = np.linspace(-90., 90., shape[1])
    lon[:] = np.linspace(-180., 180, shape[2])
    f.close()
    return filename


@pytest.fixture(scope="module")
def monthlydatetimelist():
    """list of monthly datetimes"""
    return [datetime.datetime(2000, 1, 1)
            + relativedelta.relativedelta(months=i) for i in range(12)]


@pytest.fixture(scope="module")
def foo3c(tempsrcdir):
    filename = os.path.join(tempsrcdir, 'foo_3c.nc')
    f = netCDF4.Dataset(filename, 'w', format='NETCDF3_CLASSIC')
    f.close()
    return filename


@pytest.fixture(scope="module")
def foo364(tempsrcdir):
    filename = os.path.join(tempsrcdir, 'foo_364.nc')
    f = netCDF4.Dataset(filename, 'w', format='NETCDF3_64BIT')
    f.close()
    return filename


@pytest.fixture(scope="module")
def foo4c(tempsrcdir):
    filename = os.path.join(tempsrcdir, 'foo_4c.nc')
    f = netCDF4.Dataset(filename, 'w', format='NETCDF4_CLASSIC')
    f.close()
    return filename
