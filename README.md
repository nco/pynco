# pynco

Python bindings for [NCO](http://nco.sourceforge.net/).  A fork from Ralf Mueller's [cdo-bindings](https://github.com/Try2Code/cdo-bindings).

## `pynco` - Use Python to access the power of [NCO](http://nco.sourceforge.net/)

This package contains the module python `nco`, which implements a python style access to the [NetCDF Operators (NCO)](http://nco.sourceforge.net/). NCO is a command line tool for processing netCDF data. Its main focus is climate data, but it can by used for other purposes too.


## Installation

### Conda Installation (recommended)

This will install all required and optional dependencies and is the quickest and easiest way to a working `pynco` installation.

```bash
conda install -c conda-forge pynco
```

### PyPI Installation

Please see [the requirements](#requirements) before installing

```bash
pip install nco
```

### Python Installation

Please see [the requirements](#requirements) before installing

```bash
python setup.py install
```


### Requirements

**Mandatory**

-  ***Platform***: Unix or Mac OS (Windows has not bee tested)
-  [NetCDF Operators (NCO)](http://nco.sourceforge.net/) - Version 4.6.9 or later. We don't test against every NCO version.
-  Python 3.6 or 3.7

**Recommended**

These will allow `pynco` operations to return `numpy` arrays

-  [scipy](http://docs.scipy.org/doc/scipy/reference/generated/scipy.io.netcdf.netcdf_file.html)
-  [netCDF-4](https://code.google.com/p/netcdf4-python/)
-  [numpy](http://www.numpy.org/)


## Usage

#### Importing the Nco class

```python
from nco import Nco
```

### Run operators

For python an instance has to be created first

```python
from nco import Nco
nco = Nco()
```

Now any NCO command (i.e. `ncks`, `ncra`, ...) can be called as a method of `nco`.

* Required arguments
    -  `input` - Input netcdf file name, str

* Optional arguments

    -  `output` - `str` or `list` of strings representing input netCDF filenames.  If not provided and operator returns a file (not an array or stdout text), the method will return a temporary file.
    - `debug` - `bool` or `int`, if less than 0 or True, debug statements will be turned on for NCO and NCOpy (default: `False`)
    -  `returnCdf` - `bool`, return a netCDF file handle (default: `False`)
    -  `returnArray` - `str`. return a numpy array of variable name (default: `''`)
    -  `returnMaArray` - `str`. return a numpy masked array of variable name (default: `''`)
    -  `options` - `list`, NCO input options, for example `options=['-7', '-L 1']` (default: `[]`)
    -  `Atted` - a wrapper object to be used for ncatted. Atted objects can be included in the options list
    -  `Limit` - a wrapper object for the hyperslab (`-d`) command line option
    -  `Rename` - a wrapper object for the `-d`, `-a`, `-v`, and `-g` command line options in `ncrename`
    -  `**kwargs` - any kwarg will be passed as a key, value pair to the nco command `--{key}={value}`.  This allows the user to pass any number of long name commands list in the nco help pages.


### Examples

*  File information:

    ```python
    ncdump_string = nco.ncdump(input=ifile)
    ```

*  Operators with user defined regular output files:

    ```python
    nco.ncra(input=ifile, output=ofile)
    ```

*  Use temporary output files:

    ```python
    temp_ofile = nco.ncrcat(input=ifile)
    ```

*  Set global NCO options:

    ```python
    nco.ncks(input=ifile, output=ofile, options="--netcdf4")
    ```

*  Return multi-dimension arrays:

    ```python
    temperatures = nco.ncra(input=ifile, returnArray=True).variables['T'][:]
    temperatures = nco.ncra(input=ifile, returnCdf=True).variables['T'][:]
    temperatures = nco.ncra(input=ifile, returnArray='T')
    ```

* Wrapper Objects

    The Atted opject is a convienent wrapper object to the `-a` command-line switch in ncatted.
    The Limit object is a wrapper to the `-d` command-line switch.
    The Rename is a wrapper for the `-a,  -v, -d , -g ` switches in ncrename.

    e.g  the following are equivalent:

    ```
    ncatted -a _FillValue,three_dmn,o,d,-9.91e+33 in.nc
    nco.ncatted(input="in.nc",options=[c.atted("overwrite","_FillValue","three_dmn",-9.91e+33,'d')])
    ```

## Tempfile helpers

`pynco` includes a simple tempfile wrapper, which makes life easier.  In the
absence of a specified output file, `pynco` will create a temporary file to allow the results of the task to be returned to the user.  For example:

```python
temperatures = nco.ncra(input=ifile, returnArray='T')
```

is equivalent to:

```
temperatures = nco.ncra(input=ifile, output=tempfile.mktemp(), returnArray='T')
```


##  Atted wrapper

It is sometimes more tidy to define the atted objects in a separate list then add that list the options in the nco call

```python
opt = [
    c.Atted("o", "units", "temperature", "Kelvin"),
    c.Atted("c", "min", "temperature", 0.16, 'd'),
    c.Atted("m", "max", "temperature", 283.01, 'float64'),
    c.Atted("c", "bnds", "time", [0.5, 1.5], 'f')
]
nco.ncatted(input="in.nc", options=opt)
```

You can also use keyword arguments in the call so the above options become

```python
opt = [
    c.Atted(mode="o", attName="units", varName="temperature", Value="Kelvin", sType="c"),
    c.Atted(mode="create", attName="min", varName="temperature", Value=0.16, sType='d' ),
    c.Atted(mode="modify", attName="max", varName="temperature", Value=283.01, sType='float64'),
    c.Atted(mode="create", attName="bnds", varName="time", Value=[0.5, 1.5], sType='float32')
]
nco.ncatted(input="in.nc", options=opt)
```

#### `Value`

Can be a single value or a list (or any python iterable type or a numpy array).

*  If sType **is not** included then the type is inferred from the first value in the list
*  If sType **is** included then any values in the list are **not** of sType are converted to the sType

#### `sType`

You can use the following: `f, d, l/i, s, b, ub, us, u, ll, ull`
Or their numpy equivalents: `float32, float64, int32, int16, byte, ubyte, uint16, uint32, int64, uint64`

For a netCDF3 character string use `c` or `char`
For netCDF4 string(s) use `sng` or `string`

#### `mode`

For mode you can use the single character abbreviations as per `ncatted`: `a, c, d, m, n, o` or the following words: `a)ppend, create, delete, modify, overwrite`


##  Limit and LimitSingle wrapper

The following are equivalent:

**nco**

```bash
ncks -d time,0,8,2 -d time,10 -d lat,-20.0,20.0 -d lon,50.0,350.0  -d lev,,,4
```

**pynco**

```python
opt = [
    c.Limit("time", 0, 8, 2),
    c.LimitSingle("time", 10),
    c.Limit("lat", -20.0, 20.0),
    c.Limit(dmn_name="lon", srt=50.0, end=350.0),
    c.Limit(dmn_name="lev", srd=4)
]

nco.ncks(input="in.nc", output="out.nc", options=opt)
```

##  Rename wrapper

The following are equivalent:

**`nco`**

```bash
ncrename -v p,pressure -v t,temperature in.nc
```

**`pynco`**

```python
rDict = {
    'p': 'pressure',
    't': 'temperature'
}
nco.ncrename(input="in.nc", options=[ c.Rename("variable", rDict) ])
```

Also equivalent:

**`nco`**

```bash
ncrename -d lon,longitude -d lat,latitude -v lon,longitude -v lat,latitude in.nc
```

**`pynco`**

```python
rDict = {
    'lon': 'longitude',
    'lat': 'latitude'
}
nco.ncrename(input="in.nc", options=[ c.Rename("d", rDict), c.Rename("v", rDict) ])
```

## Support, Issues, Bugs, ...

Please use the github page to report issues/bugs/features: https://github.com/nco/pynco.

For usage questions, please use [Stack Overflow](https://stackoverflow.com/questions/tagged/nco).


## License

`pynco` makes use of the MIT License, see LICENSE.txt.


## Other stuff

* Requires: NCO version 4.6.9 or newer, Python 3.6 or later
* Optional: scipy or Python netCDF4
