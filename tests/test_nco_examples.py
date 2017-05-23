"""
Test that nco.py works for documented examples from NCO.

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
import pytest
import os
from nco import Nco


@pytest.mark.usefixtures("cleandir")
def test_ncks_hdf2nc(hdf_file):
    """
    1.6 netCDF2/3/4 and HDF4/5 Support
    Converting HDF4 files to netCDF: Since NCO reads HDF4 files natively,
    it is now easy to convert HDF4 files to netCDF files directly, e.g.,

    ncks        fl.hdf fl.nc # Convert HDF4->netCDF4 (NCO 4.4.0+, netCDF4.3.1+)
    ncks --hdf4 fl.hdf fl.nc # Convert HDF4->netCDF4 (NCO 4.3.7-4.3.9)
    """
    if hdf_file is None:
        pytest.skip('Skipped because h5py is not installed')
    nco = Nco(debug=True)
    nco.ncks(input=hdf_file, output='foo.nc')
    nco.ncks(input=hdf_file, output='foo.nc', hdf4=True)


def test_ncks_hdf2nc3(hdf_file):
    """
    1.6 netCDF2/3/4 and HDF4/5 Support
    Obtaining a netCDF3 file from an HDF4 is now easy, even though the HDF4
    file may contain netCDF4 atomic types (e.g., unsigned bytes,
    64-bit integers):

    ncks -3 fl.hdf fl.nc      # HDF4->netCDF3 (NCO 4.4.0+, netCDF 4.3.1+)
    ncks -7 -L 1 fl.hdf fl.nc # HDF4->netCDF4 (NCO 4.4.0+, netCDF 4.3.1+)
    ncks --hdf4 -3 fl.hdf fl.nc # HDF4->netCDF3 (netCDF 4.3.0-)
    ncks --hdf4 -7 fl.hdf fl.nc # HDF4->netCDF4 classic (netCDF 4.3.0-)
    """
    if hdf_file is None:
        pytest.skip('Skipped because h5py is not installed')
    nco = Nco(debug=True)
    nco.ncks(input=hdf_file, output='foo.nc', options=['-3'])
    nco.ncks(input=hdf_file, output='foo.nc', options=['-7 -L 1'])
    nco.ncks(input=hdf_file, output='foo.nc', options=['-3'], hdf4=True)
    nco.ncks(input=hdf_file, output='foo.nc', options=['-7'], hdf4=True)


def test_temp_output_files(foo_nc):
    """
    2.3 Temporary Output Files
    ncks in.nc out.nc # Default: create out.pid.tmp.nc then move to out.nc
    ncks --wrt_tmp_fl in.nc out.nc # Same as default
    ncks --no_tmp_fl in.nc out.nc # Create out.nc directly on disk
    ncks --no_tmp_fl in.nc in.nc # ERROR-prone! Overwrite in.nc with itself
    ncks --create_ram --no_tmp_fl in.nc in.nc # Create in RAM, write to disk
    ncks --open_ram --no_tmp_fl in.nc in.nc # Read into RAM, write to disk
    """
    nco = Nco(debug=True)
    nco.ncks(input=foo_nc, output='bar.nc')
    nco.ncks(input=foo_nc, output='bar.nc', wrt_tmp_fl=True)
    nco.ncks(input=foo_nc, output='bar.nc', no_tmp_fl=True)
    nco.ncks(input=foo_nc, output=foo_nc, no_tmp_fl=True, create_ram=True)
    nco.ncks(input=foo_nc, output=foo_nc, no_tmp_fl=True, open_ram=True)


def test_ncks_append_variables(foo_nc, bar_nc):
    """
    2.4 Appending Variables
    The simplest way to create the union of two files is

    ncks -A fl_1.nc fl_2.nc
    """
    nco = Nco(debug=True)
    nco.ncks(input=foo_nc, output=bar_nc, options=['-A'])
    nco.ncks(input=foo_nc, output=bar_nc, append=True)
    nco.ncks(input=foo_nc, output=bar_nc, apn=True)
    nco.ncks(input=foo_nc, output=bar_nc)

# def test_add_record_dimension():
#     """
#     2.6.1 Concatenators ncrcat and ncecat
#     """
#     nco = Nco(debug=True)
#     outfiles = []
#     for idx in xrange(1, 11):
#         infile = 'x_{:2}.nc'.format()
#         outfile = 'foo_{:2}.nc'.format()
#         nco.ncpdq(input=infile, output=outfile, arrange='x,time')
#         outfiles.append(outfile)
#     nco.ncrcat(input=outfiles, output='out.nc')
#     nco.ncpdq(input='out.nc', output='out.nc', arrange='time,x')

# def test_openMP_threading():
#     pass


def test_command_line_options(foo_nc):
    """
    3.4 Command Line Options

    ncks -D 3 in.nc        # Short option
    ncks --dbg_lvl=3 in.nc # Long option, preferred form
    ncks --dbg_lvl 3 in.nc # Long option, alternate form
    """
    nco = Nco(debug=True)
    nco.ncks(input=foo_nc, options=['-D 3'])
    nco.ncks(input=foo_nc, options=['--dbg_lvl=3'])
    nco.ncks(input=foo_nc, options=['--dbg_lvl 3'])
    nco.ncks(input=foo_nc, dbg_lvl=3)


def test_specifying_input_files(testfiles8589):
    """
    3.5 Specifying Input Files

    ncra 85.nc 86.nc 87.nc 88.nc 89.nc 8589.nc
    ncra 8[56789].nc 8589.nc
    ncra -p input-path 85.nc 86.nc 87.nc 88.nc 89.nc 8589.nc
    ncra -n 5,2,1 85.nc 8589.nc
    """
    inputs = ['85.nc', '86.nc', '87.nc', '88.nc', '89.nc']
    nco = Nco(debug=True)
    nco.ncra(input=inputs, ouptut='8589.nc')
    nco.ncra(input='8[56789].nc', ouptut='8589.nc')
    srcdir = os.path.split(inputs[0])
    nco.ncra(input=inputs, ouptut='8589.nc', path=srcdir)
    nco.ncra(input=inputs, ouptut='8589.nc', nintap='5,2,1')


def test_determining_file_format(foo3c, foo364, foo4c, hdf_file):
    """
    3.9.2 Determining File Format

    ncks -M foo_3c.nc
    ncks -M foo_364.nc
    ncks -M foo_4c.nc
    ncks -M foo_4.nc
    ncks -D 2 -M hdf.hdf
    # ncks -D 2 -M http://thredds-test.ucar.edu/thredds/dodsC/testdods/in.nc
    ncks -D 2 -M foo_4.nc
    """
    nco = Nco(debug=True)
    nco.ncks(input=foo3c, options=['-M'])
    nco.ncks(input=foo364, options=['-M'])
    nco.ncks(input=foo4c, options=['-M'])
    nco.ncks(input=foo4c, options=['-D 2 -M'])

    if hdf_file is not None:
        assert os.path.isfile(hdf_file)
        nco.ncks(input=hdf_file, options=['-D 2 -M'])
    # nco.ncks(input='http://thredds-test.ucar.edu/thredds/dodsC/testdods/in.nc',
    #          options=['-D 2', '-M']) # does not work from command line either


def test_file_conversion(foo3c, foo4c):
    """
    3.9.2 Determining File Format

    ncks --fl_fmt=classic in.nc foo_3c.nc # netCDF3 classic
    ncks --fl_fmt=64bit in.nc foo_364.nc # netCDF3 64bit
    ncks --fl_fmt=netcdf4_classic in.nc foo_4c.nc # netCDF4 classic
    ncks --fl_fmt=netcdf4 in.nc foo_4.nc # netCDF4
    ncks -3 in.nc foo_3c.nc # netCDF3 classic
    ncks --3 in.nc foo_3c.nc # netCDF3 classic
    ncks -6 in.nc foo_364.nc # netCDF3 64bit
    ncks --64 in.nc foo_364.nc # netCDF3 64bit
    ncks -4 in.nc foo_4.nc # netCDF4
    ncks --4 in.nc foo_4.nc # netCDF4
    ncks -7 in.nc foo_4c.nc # netCDF4 classic
    ncks --7 in.nc foo_4c.nc # netCDF4 classic
    """
    nco = Nco(debug=True)
    nco.ncks(input=foo4c, output='foo_3c.nc', fl_fmt='classic')
    nco.ncks(input=foo4c, output='foo_364.nc', fl_fmt='64bit')
    nco.ncks(input=foo3c, output='foo_4c.nc', fl_fmt='netcdf4_classic')
    nco.ncks(input=foo3c, output='foo_4.nc', fl_fmt='netcdf4')
    nco.ncks(input=foo4c, output='foo_3c.nc', options=['-3'])
    nco.ncks(input=foo4c, output='foo_3c.nc', options=['--3'])
    nco.ncks(input=foo3c, output='foo_364c.nc', options=['-6'])
    nco.ncks(input=foo3c, output='foo_364c.nc', options=['--64'])
    nco.ncks(input=foo3c, output='foo_4.nc', options=['-4'])
    nco.ncks(input=foo3c, output='foo_4.nc', options=['--4'])
    nco.ncks(input=foo3c, output='foo_4c.nc', options=['-7'])
    nco.ncks(input=foo3c, output='foo_4c.nc', options=['--7'])


def test_hyperslabs(testfileglobal):
    """
    3.15 Hyperslabs

    # First and second indices of lon dimension
    ncks -F -d lon,1,2 in.nc out.nc
    # Second and third indices of lon dimension
    ncks -d lon,1,2 in.nc out.nc
    # All longitude values between 1 and 2 degrees
    ncks -d lon,1.0,2.0 in.nc out.nc
    # All longitude values between 1 and 2 degrees
    ncks -F -d lon,1.0,2.0 in.nc out.nc
    # Every other longitude value between 0 and 90 degrees
    ncks -F -d lon,0.0,90.0,2 in.nc out.nc
    # Last two indices of lon dimension
    ncks -F -d lon,1,-2 in.nc out.nc
    # Third-to-last to last index of lon dimension
    ncks -F -d lon,-3,-1 in.nc out.nc
    # Third-to-last to last index of lon dimension
    ncks -F -d lon,-3, in.nc out.nc
    """
    nco = Nco(debug=True)
    nco.ncks(input=testfileglobal, output='out.nc', fortran=True,
             dimension='lon,1,2')
    nco.ncks(input=testfileglobal, output='out.nc',
             dimension='lon,1,2')
    nco.ncks(input=testfileglobal, output='out.nc', fortran=True,
             dimension='lon,1.0,2.0')
    nco.ncks(input=testfileglobal, output='out.nc', fortran=True,
             dimension='lon,0.0,90.0,2')
    nco.ncks(input=testfileglobal, output='out.nc', fortran=True,
             dimension='lon,1,-2')
    nco.ncks(input=testfileglobal, output='out.nc', fortran=True,
             dimension='lon,-3,-1')
    nco.ncks(input=testfileglobal, output='out.nc', fortran=True,
             dimension='lon,-3')
