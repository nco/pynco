# pynco

Python bindings for [NCO](http://nco.sourceforge.net/).  A fork from Ralf Mueller's [cdo-bindings](https://github.com/Try2Code/cdo-bindings).

This package contains the module python `nco`, which implements a python style access to the [NetCDF Operators (NCO)](http://nco.sourceforge.net/). NCO is a command line tool for processing netCDF data. Its main focus is climate data, but it can by used for other purposes too.


## Installation

### Conda Installation (recommended)

This will install all required and optional dependencies and is the quickest and easiest way to a working `pynco` installation.

```bash
$ conda install -c conda-forge pynco
```

### Python installation

Please see [the requirements](#requirements) before installing

```bash
$ pip install nco
```


### Requirements

**Mandatory**

-  ***Platform***: Unix or Mac OS (Windows has not been tested)
-  [NetCDF Operators (NCO)](http://nco.sourceforge.net/) - Version 4.6.9 or later. We don't test against every NCO version.
-  Python 3.7 or later

**Recommended**

These will allow `pynco` operations to return `numpy` arrays

-  [scipy](http://scipy.org/)
-  [netCDF4](https://unidata.github.io/netcdf4-python/)


## Usage

### The `Nco` class

An instance of the `Nco` class is required to access all `nco` commands.

```python
from nco import Nco
nco = Nco()
```

Now any NCO command (i.e. `ncks`, `ncra`, ...) can be called as a method of `nco`.
See the examples for usage.

### Arguments

#### Required arguments

-  `input` - Input netcdf file name, str

#### Optional arguments

- `output` - `str` or `list` of strings representing output netCDF filenames.  If not provided and operator returns a file (not an array or stdout text), the method will return a temporary file.
- `debug` - `bool` or `int`, if less than 0 or True, debug statements will be turned on for NCO and NCOpy (default: `False`)
- `returnCdf` - `bool`, return a netCDF file handle (default: `False`)
- `returnArray` - `str`. return a numpy array of variable name (default: `''`)
- `returnMaArray` - `str`. return a numpy masked array of variable name (default: `''`)
- `use_shell` - `bool`. use shell to execute commands, useful if you need to pass wildcards or other characters in arguments that can be expanded by shell interpretor (default: `False`)
- `options` - `list`, NCO input options, for example `options=['-7', '-L 1']` (default: `[]`).
- `**kwargs` - any kwarg will be passed to the nco command as `--{key}={value}`.  This allows the user to pass any number of long name commands list in the nco help pages.


### Examples

####  File information

```python
ncdump_string = nco.ncdump(input=ifile)
```

####  Operators with user defined regular output files

```python
nco.ncra(input=ifile, output=ofile)
```

####  Use temporary output files

```python
temp_ofile = nco.ncrcat(input=ifile)
```

####  Set global NCO options

```python
nco.ncks(input=ifile, output=ofile, options="--netcdf4")
```

####  Return multi-dimension arrays

```python
temperatures = nco.ncra(input=ifile, returnArray=True).variables['T'][:]
temperatures = nco.ncra(input=ifile, returnCdf=True).variables['T'][:]
temperatures = nco.ncra(input=ifile, returnArray='T')
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

## Complex command helpers

`pynco` provides some tools to make complicated command line flags in `ncatted`, `ncks`, and `ncrename` easier. These helpers can be imported from `nco.custom`:

```python
from nco.custom import Atted, Limit, LimitSingle, Rename
```

The Atted class helps with the `ncatted` command.
The Limit and LimitSingle classes help with the the `-d` option for `ncks`.
The Rename class helps with the `-a,  -v, -d , -g ` options for `ncrename`.

The following are equivalent calls to `ncatted`:

**nco**

```bash
ncatted -a _FillValue,three_dmn,o,d,-9.91e+33 in.nc
```

**pynco**

```python
from nco import Nco
from nco.custom import Atted

nco = Nco()
nco.ncatted(input="in.nc",options=[
    Atted(
        mode="overwrite",
        att_name="_FillValue",
        var_name="three_dmn",
        value=-9.91e+33,
        stype='d',
    ),
])
```


### Atted

The Atted object is a helper for the `-a` command-line switch in ncatted:

```python
from nco import Nco
from nco.custom import Atted

nco = Nco()
opt = [
    Atted("o", "units", "temperature", "Kelvin"),
    Atted("c", "min", "temperature", 0.16, 'd'),
    Atted("m", "max", "temperature", 283.01, 'float64'),
    Atted("c", "bnds", "time", [0.5, 1.5], 'f')
]
nco.ncatted(input="in.nc", options=opt)
```

Using keyword arguments can add even more clarity:

```python
from nco import Nco
from nco.custom import Atted

nco = Nco()
opt = [
    Atted(mode="overwrite", att_name="units", var_name="temperature", value="Kelvin", stype="c"),
    Atted(mode="create", att_name="min", var_name="temperature", value=0.16, stype='d' ),
    Atted(mode="modify", att_name="max", var_name="temperature", value=283.01, stype='float64'),
    Atted(mode="create", att_name="bnds", var_name="time", value=[0.5, 1.5], stype='float32')
]
nco.ncatted(input="in.nc", options=opt)
```

`mode` can be the single character abbreviations as per `ncatted`: `a, c, d, m, n, o` or the long form equivalents `append, create, delete, modify, overwrite`.

`value` can be a single value, a list, iterable, or a numpy array.

`stype` can be one of the following strings: `f, d, l/i, s, b, ub, us, u, ll, ull`
or their numpy equivalents: `float32, float64, int32, int16, byte, ubyte, uint16, uint32, int64, uint64`.

If stype **is not** included then the type is inferred from the first value in the list.
If stype **is** included then any values in the list are **not** of stype are converted to the stype.

For a netCDF3 character string use `c` or `char`.
For netCDF4 string(s) use `sng` or `string`.

### Limit and LimitSingle

The following are equivalent:

**nco**

```bash
ncks -d time,0,8,2 -d time,10 -d lat,-20.0,20.0 -d lon,50.0,350.0  -d lev,,,4
```

**pynco**

```python
from nco import Nco
from nco.custom import Limit, LimitSingle

nco = Nco()
opt = [
    Limit("time", 0, 8, 2),
    LimitSingle("time", 10),
    Limit("lat", -20.0, 20.0),
    Limit(dmn_name="lon", srt=50.0, end=350.0),
    Limit(dmn_name="lev", srd=4)
]
nco.ncks(input="in.nc", output="out.nc", options=opt)
```

### Rename wrapper

The following are equivalent:

**nco**

```bash
ncrename -v p,pressure -v t,temperature in.nc
```

**pynco**

```python
from nco import Nco
from nco.custom import Rename

nco = Nco()
rDict = {
    'p': 'pressure',
    't': 'temperature'
}
nco.ncrename(input="in.nc", options=[ Rename("variable", rDict) ])
```

Also equivalent:

**nco**

```bash
ncrename -d lon,longitude -d lat,latitude -v lon,longitude -v lat,latitude in.nc
```

**pynco**

```python
rDict = {
    'lon': 'longitude',
    'lat': 'latitude'
}
nco.ncrename(input="in.nc", options=[ Rename("d", rDict), Rename("v", rDict) ])
```

## Support, issues, bugs, ...

Please use the [github page](https://github.com/nco/pynco) to report issues, bugs, and features.

For usage questions, please use [Stack Overflow](https://stackoverflow.com/questions/tagged/nco).

## License

`pynco` makes use of the MIT License, see LICENSE.txt.
