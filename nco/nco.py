"""
nco module.  Use Nco class as interface.

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
import re
import subprocess
import tempfile
import random
from distutils.version import LooseVersion


class NCOException(Exception):
    def __init__(self, stdout, stderr, returncode):
        super(NCOException, self).__init__()
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.msg = '(returncode:{0}) {1}'.format(returncode, stderr)

    def __str__(self):
        return self.msg

class Nco(object):
    def __init__(self, returnCdf=False, returnNoneOnError=False,
                 forceOutput=True, cdfMod='netcdf4', debug=0, **kwargs):

        operators = ['ncap2', 'ncatted', 'ncbo', 'nces', 'ncecat', 'ncflint',
                     'ncks', 'ncpdq', 'ncra', 'ncrcat', 'ncrename', 'ncwa',
                     'ncea', 'ncdump']

        if 'NCOpath' in os.environ:
            self.NCOpath = os.environ['NCOpath']
        else:
            self.NCOpath = os.path.split(which('ncks'))[0]

        self.operators = operators
        self.returnCdf = returnCdf
        self.returnNoneOnError = returnNoneOnError
        self.tempfile = MyTempfile()
        self.forceOutput = forceOutput
        self.cdfMod = cdfMod
        self.debug = debug
        self.outputOperatorsPattern = ['ncdump', '-H', '--data',
                                       '--hieronymus', '-M', '--Mtd',
                                       '--Metadata', '-m', '--mtd',
                                       '--metadata', '-P', '--prn', '--print',
                                       '-r', '--revision', '--vrs',
                                       '--version', '--u', '--units']
        self.OverwriteOperatorsPattern = ['-O', '--ovr', '--overwrite']
        self.AppendOperatorsPattern = ['-A', '--apn', '--append']
        self.DontForcePattern = (self.outputOperatorsPattern +
                                 self.OverwriteOperatorsPattern +
                                 self.AppendOperatorsPattern)
        # I/O from call
        self.returncode = 0
        self.stdout = ""
        self.stderr = ""

        if kwargs:
            self.options = kwargs
        else:
            self.options = None

    def __dir__(self):
        res = dir(type(self)) + list(self.__dict__.keys())
        res.extend(self.operators)
        return res

    def call(self, cmd, inputs=None, environment=None):

        inline_cmd = cmd
        if inputs is not None:
            if isinstance(inputs, str):
                inline_cmd.append(inputs)
            else:
                #we assume it's either a list, a tuple or any iterable.
                inline_cmd.extend(inputs)

        if self.debug:
            print('# DEBUG ==================================================')
            if environment:
                for key, val in list(environment.items()):
                    print("# DEBUG: ENV: {0} = {1}".format(key, val))
            print('# DEBUG: CALL>> {0}'.format(' '.join(inline_cmd)))
            print('# DEBUG ==================================================')

        try:
            proc = subprocess.Popen(' '.join(inline_cmd),
                                    shell=True,
                                    stderr=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    env=environment)
        except OSError:
            # Argument list may have been too long, so don't use a shell
            proc = subprocess.Popen(inline_cmd,
                                    stderr=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    env=environment)
        retvals = proc.communicate()
        return {"stdout": retvals[0],
                "stderr": retvals[1],
                "returncode": proc.returncode}

    def hasError(self, method_name, inputs, cmd, retvals):
        if (self.debug):
            print("# DEBUG: RETURNCODE: {0}".format(retvals["returncode"]))
        if retvals["returncode"] != 0:
            print("Error in calling operator {0} with:".format(method_name))
            print(">>> {0} <<<".format(' '.join(cmd)))
            print("Inputs: {0!s}".format(inputs))
            print(retvals["stderr"])
            return True
        else:
            return False

    def __getattr__(self, method_name):

        @auto_doc(method_name, self)
        def get(self, input, **kwargs):
            options = kwargs.pop('options', False)
            force = kwargs.pop("force", self.forceOutput)
            output = kwargs.pop("output", None)
            environment = kwargs.pop("env", None)
            debug = kwargs.pop("debug", self.debug)
            returnCdf = kwargs.pop("returnCdf", False)
            returnArray = kwargs.pop("returnArray", False)
            returnMaArray = kwargs.pop("returnMaArray", False)
            operatorPrintsOut = kwargs.pop("operatorPrintsOut", False)

            #build the nco command
            #1. the nco operator
            cmd = [os.path.join(self.NCOpath, method_name)]

            #2a. options keyword arg
            if options:
                if isinstance(options, str):
                    cmd.extend(options.split())
                else:
                    #we assume it's either a list, a tuple or any iterable.
                    cmd.extend(options)

            if debug:
                if type(debug) == bool:
                    # assume debug level is 3
                    cmd.append('--nco_dbg_lvl=3')
                elif type(debug) == int:
                    cmd.append('--nco_dbg_lvl={0}'.format(debug))
                else:
                    raise TypeError('Unknown type for debug: \
                                    {0}'.format(type(debug)))

            if output and force and os.path.isfile(output):
                # make sure overwrite is set
                if debug:
                    print("Overwriting file: {0}".format(output))
                if any([i for i in cmd if i in self.DontForcePattern]):
                    force = False
            else:
                force = False

            #2b. all other keyword args become options
            if kwargs:
                for key, val in list(kwargs.items()):
                    if val and type(val) == bool:
                        cmd.append("--{0}".format(key))
                        if cmd[-1] in (self.DontForcePattern):
                            force = False
                    elif isinstance(val, str) or \
                            isinstance(val, int) or \
                            isinstance(val, float):
                        cmd.append("--{0}={1}".format(key, val))
                    else:
                        #we assume it's either a list, a tuple or any iterable.
                        cmd.append("--{0}={1}".format(key, ",".join(val)))

            #2c. Global options come in
            if self.options:
                for key, val in list(self.options.items()):
                    if val and type(val) == bool:
                        cmd.append("--"+key)
                    elif isinstance(val, str):
                        cmd.append("--{0}={1}".format(key, val))
                    else:
                        #we assume it's either a list, a tuple or any iterable.
                        cmd.append("--{0}={1}".format(key, ",".join(val)))

            # 3.  Add in overwrite if necessary
            if force:
                cmd.append('--overwrite')

            # Check if operator appends
            operatorAppends = False
            for piece in cmd:
                if piece in self.AppendOperatorsPattern:
                    operatorAppends = True

            # If operator appends and NCO version >= 4.3.7, remove -H -M -m
            # and their ancillaries from outputOperatorsPattern
            if operatorAppends and method_name == 'ncks':
                nco_version = self.version()
                if LooseVersion(nco_version) >= LooseVersion('4.3.7'):
                    self.outputOperatorsPattern = ['ncdump', '-r',
                                                   '--revision', '--vrs',
                                                   '--version']

            # Check if operator prints out
            for piece in cmd:
                if piece in self.outputOperatorsPattern or \
                        method_name == 'ncdump':
                    operatorPrintsOut = True

            if operatorPrintsOut:
                retvals = self.call(cmd, inputs=input)
                self.returncode = retvals["returncode"]
                self.stdout = retvals["stdout"]
                self.stderr = retvals["stderr"]
                if not self.hasError(method_name, input, cmd, retvals):
                    return retvals["stdout"]
                    # parsing can be done by 3rd party
                else:
                    if self.returnNoneOnError:
                        return None
                    else:
                        raise NCOException(**retvals)
            else:
                if output:
                    if isinstance(output, str):
                        cmd.append("--output={0}".format(output))
                    else:
                        # we assume it's an iterable.
                        if len(output) > 1:
                            raise TypeError('Only one output allowed, \
                                            must be string or 1 length \
                                            iterable. Recieved output: {0} \
                                            with a type of \
                                            {1}'.format(output,
                                                        type(output)))
                        cmd.extend("--output={0}".format(output))
                else:
                    output = self.tempfile.path()
                    cmd.append("--output={0}".format(output))

                retvals = self.call(cmd, inputs=input, environment=environment)
                self.returncode = retvals["returncode"]
                self.stdout = retvals["stdout"]
                self.stderr = retvals["stderr"]
                if self.hasError(method_name, input, cmd, retvals):
                    if self.returnNoneOnError:
                        return None
                    else:
                        raise NCOException(**retvals)

            if returnArray:
                return self.readArray(output, returnArray)
            elif returnMaArray:
                return self.readMaArray(output, returnMaArray)
            elif self.returnCdf or returnCdf:
                if not self.returnCdf:
                    self.loadCdf()
                    return self.readCdf(output)
            else:
                return output

        if (method_name in self.__dict__) or \
           (method_name in self.operators):
            if self.debug:
                print("Found method: {0}".format(method_name))
            #cache the method for later
            setattr(self.__class__, method_name, get)
            return get.__get__(self)
        else:
            # If the method isn't in our dictionary, act normal.
            print("#=====================================================")
            print("Cannot find method: {0}".format(method_name))
            raise AttributeError("Unknown method {0}!".format(method_name))

    def loadCdf(self):
        if self.cdfMod == "netcdf4":
            try:
                import netCDF4 as cdf
                self.cdf = cdf
            except:
                raise ImportError("Could not load python-netcdf4 - try to "
                                  "setting 'cdfMod='scipy'")
        elif self.cdfMod == "scipy":
            try:
                import scipy.io.netcdf as cdf
                self.cdf = cdf
            except:
                raise ImportError("Could not load scipy.io.netcdf - try to "
                                  "setting 'cdfMod='netcdf4'")
        else:
            raise ValueError("Unknown value provided for cdfMod.  Valid "
                             "values are 'scipy' and 'netcdf4'")

    def setReturnArray(self, value=True):
        self.returnCdf = value
        if value:
            self.loadCdf()

    def unsetReturnArray(self):
        self.setReturnArray(False)

    def hasNco(self, path=None):
        if path is None:
            path = self.NCOpath

        if os.path.isdir(path) and os.access(path, os.X_OK):
            return True
        else:
            return False

    def checkNco(self):
        if self.hasNco():
            call = [os.path.join(self.NCOpath, 'ncra'), '--version']
            proc = subprocess.Popen(' '.join(call),
                                    shell=True,
                                    stderr=subprocess.PIPE,
                                    stdout=subprocess.PIPE)
            retvals = proc.communicate()
            print(retvals)

    def setNco(self, value):
        self.NCOpath = value

    def getNco(self):
        return self.NCOpath

    #==================================================================
    # Addional operators:
    #------------------------------------------------------------------
    def module_version(self):
        return '0.0.0'

    def version(self):
        # return NCO's version
        proc = subprocess.Popen([os.path.join(self.NCOpath, 'ncra'),
                                 '--version'],
                                stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE)
        ret = proc.communicate()
        ncra_help = ret[1]
        match = re.search('NCO netCDF Operators version (\d.*) ',
                          ncra_help)
        # some versions write version information in quotation marks
        if not match:
            match = re.search('NCO netCDF Operators version "(\d.*)" ',
                              ncra_help)
        return match.group(1).split(' ')[0]

    def readCdf(self, infile):
        """Return a cdf handle created by the available cdf library.
        python-netcdf4 and scipy suported (default:scipy)"""
        if not self.returnCdf:
            self.loadCdf()

        if self.cdfMod == "scipy":
            #making it compatible to older scipy versions
            fileObj = self.cdf.netcdf_file(infile, mode='r')
        elif self.cdfMod == "netcdf4":
            fileObj = self.cdf.Dataset(infile)
        else:
            raise ImportError("Could not import data \
                              from file {0}".format(infile))
        return fileObj

    def openCdf(self, infile):
        """Return a cdf handle created by the available cdf library.
        python-netcdf4 and scipy suported (default:scipy)"""
        if not self.returnCdf:
            self.loadCdf()

        if self.cdfMod == "scipy":
            #making it compatible to older scipy versions
            print("Use scipy")
            fileObj = self.cdf.netcdf_file(infile, mode='r+')
        elif self.cdfMod == "netcdf4":
            print("Use netcdf4")
            fileObj = self.cdf.Dataset(infile, 'r+')
        else:
            raise ImportError("Could not import data \
                              from file: {0}".format(infile))

        return fileObj

    def readArray(self, infile, varname):
        """Directly return a numpy array for a given variable name"""
        filehandle = self.readCdf(infile)
        try:
            # return the data array
            return filehandle.variables[varname][:]
        except KeyError:
            print("Cannot find variable: {0}".format(varname))
            raise KeyError

    def readMaArray(self, infile, varname):
        """Create a masked array based on cdf's FillValue"""
        fileObj = self.readCdf(infile)

        #.data is not backwards compatible to old scipy versions, [:] is
        data = fileObj.variables[varname][:]

        # load numpy if available
        try:
            import numpy as np
        except:
            raise ImportError("numpy is required to return masked arrays.")

        if hasattr(fileObj.variables[varname], '_FillValue'):
            # return masked array
            fill_val = fileObj.variables[varname]._FillValue
            retval = np.ma.masked_where(data == fill_val, data)
        else:
            #generate dummy mask which is always valid
            retval = np.ma.array(data)

        return retval


class MyTempfile(object):
    """Helper module for easy temp file handling"""
    __tempfiles = []

    def __init__(self):
        self.persistent_tempfile = False

    def __del__(self):
        # remove temporary files
        for filename in self.__class__.__tempfiles:
            if os.path.isfile(filename):
                os.remove(filename)

    def setPersist(self, value):
        self.persistent_tempfiles = value

    def path(self):
        if not self.persistent_tempfile:
            t = tempfile.NamedTemporaryFile(delete=True, prefix='nco.py_',
                                            suffix='.nco.tmp')
            self.__class__.__tempfiles.append(t.name)
            t.close()

            return t.name
        else:
            N = 10000000
            t = "{0}".format(random.randint(N))


def auto_doc(tool, nco_self):
    """Generate the __doc__ string of the decorated function by
    calling the nco help command"""
    def desc(func):
        func.__doc__ = nco_self.call([tool, '--help']).get('stdout')
        return func
    return desc


def which(pgm):
    path = os.getenv('PATH')
    for p in path.split(os.path.pathsep):
        p = os.path.join(p, pgm)
        if os.path.exists(p) and os.access(p, os.X_OK):
            return p
    return None
