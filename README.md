# pynco

Python bindings for [NCO](http://nco.sourceforge.net/).  A fork from Ralf Mueller's [cdo-bindings](https://github.com/Try2Code/cdo-bindings).

This package contains the python module `nco`, which implements a python style access to the [NetCDF Operators (NCO)](http://nco.sourceforge.net/). NCO is a command line tool for processing netCDF data. Its main focus is climate data, but it can by used for other purposes too.


## Documentation

Read the documentation at [pynco.readthedocs.org](https://pynco.readthedocs.io/)

## Installation

### Conda Installation (recommended)

This will install all required and optional dependencies and is the quickest and easiest way to a working `pynco` installation.

```bash
conda install -c conda-forge pynco
```
### PyPI Installation

Please see [the requirements](https://pynco.readthedocs.org/en/latest/#requirements) before installing

```bash
pip install nco
```
## Example

```python
from nco import Nco
nco = Nco()
temperatures = nco.ncra(input='input.nc', returnCdf=True).variables['T'][:]
```
## Support, issues, bugs, ...

Please use the github page to report issues, bugs, and features:
https://github.com/nco/pynco.

For usage questions, please use [Stack Overflow](https://stackoverflow.com/questions/tagged/nco).

## License

`pynco` makes use of the MIT License, see LICENSE.txt.
