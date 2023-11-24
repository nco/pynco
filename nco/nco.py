"""
nco module.  Use Nco class as interface.
"""
import shutil
import os.path
import re
import shlex
import subprocess
import tempfile
from packaging.version import parse as parse_version


class NCOException(Exception):
    def __init__(self, stdout, stderr, returncode):
        super(NCOException, self).__init__()
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.msg = "(returncode:{0}) {1}".format(returncode, stderr)

    def __str__(self):
        return self.msg


class Nco(object):
    def __init__(
        self,
        returnCdf=False,
        return_none_on_error=False,
        force_output=True,
        cdf_module="netcdf4",
        debug=0,
        **kwargs
    ):

        operators = [
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
            "ncea",
        ]

        if "NCOpath" in os.environ:
            self.nco_path = os.environ["NCOpath"]
        else:
            self.nco_path = os.path.split(shutil.which("ncks"))[0]

        self.operators = operators
        self.return_cdf = returnCdf
        self.return_none_on_error = return_none_on_error
        self.force_output = force_output
        self.cdf_module = cdf_module
        self.debug = debug
        self.outputOperatorsPattern = [
            "-H",
            "--data",
            "--hieronymus",
            "-M",
            "--Mtd",
            "--Metadata",
            "-m",
            "--mtd",
            "--metadata",
            "-P",
            "--prn",
            "--print",
            "-r",
            "--revision",
            "--vrs",
            "--version",
            "--u",
            "--units",
        ]
        self.OverwriteOperatorsPattern = ["-O", "--ovr", "--overwrite"]
        self.AppendOperatorsPattern = ["-A", "--apn", "--append"]
        # operators that can function with a single file
        self.SingleFileOperatorsPattern = ["ncap2", "ncatted", "ncks", "ncrename"]
        self.DontForcePattern = (
            self.outputOperatorsPattern
            + self.OverwriteOperatorsPattern
            + self.AppendOperatorsPattern
        )
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

    def call(self, cmd, inputs=None, environment=None, use_shell=False):

        cmd = list(cmd)
        if inputs is not None:
            if isinstance(inputs, str):
                cmd.append(inputs)
            else:
                # assume it's an iterable
                cmd.extend(inputs)

        if self.debug:
            print("# DEBUG ==================================================")
            if environment:
                for key, val in list(environment.items()):
                    print("# DEBUG: ENV: {0} = {1}".format(key, val))
            print("# DEBUG: CALL>> {0}".format(" ".join(map(shlex.quote, cmd))))
            print("# DEBUG ==================================================")

        # if we're using the shell then we need to pass a single string as the
        # command rather than in iterable
        if use_shell:
            shell_cmd = " ".join(map(shlex.quote, cmd))
            try:
                proc = subprocess.Popen(
                    shell_cmd,
                    shell=True,
                    stdin=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    env=environment,
                )
            except OSError:
                # Argument list may have been too long, so don't use a shell
                use_shell = False

        if not use_shell:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                env=environment,
            )

        retvals = proc.communicate()
        return {
            "stdout": retvals[0],
            "stderr": retvals[1],
            "returncode": proc.returncode,
        }

    def has_error(self, method_name, inputs, cmd, retvals):
        if self.debug:
            print(
                "# DEBUG: RETURNCODE: {return_code}".format(
                    return_code=retvals["returncode"]
                )
            )
        if retvals["returncode"] != 0:
            print("Error in calling operator {method} with:".format(
                method=method_name))
            print(">>> {command} <<<".format(
                command=" ".join(map(shlex.quote, cmd))))
            print("Inputs: {0!s}".format(inputs))
            print(retvals["stderr"])
            return True
        else:
            return False

    def __getattr__(self, nco_command):

        # act normal if this is not an nco operator
        if nco_command not in self.operators:
            raise AttributeError("Unknown operator: {0}".format(nco_command))

        @auto_doc(nco_command, self)
        def get(self, input, **kwargs):
            """
            This is the function that's called when this __getattr__
            "magic" function runs. Parses options and constructs/calls
            an appropriate/corresponding NCO command.

            :param self:
            :param input:
            :param kwargs:
            :return:
            """
            options = kwargs.pop("options", [])
            force = kwargs.pop("force", self.force_output)
            output = kwargs.pop("output", None)
            environment = kwargs.pop("env", None)
            debug = kwargs.pop("debug", self.debug)
            return_cdf = kwargs.pop("returnCdf", False)
            return_array = kwargs.pop("returnArray", False)
            return_ma_array = kwargs.pop("returnMaArray", False)
            operator_prints_out = kwargs.pop("operator_prints_out", False)
            use_shell = kwargs.pop("use_shell", False)

            # build the NCO command
            # 1. the NCO operator
            cmd = [os.path.join(self.nco_path, nco_command)]

            if options:
                for option in options:
                    if isinstance(option, str):
                        cmd.extend(shlex.split(option))
                    elif hasattr(option, "prn_option"):
                        cmd.extend(option.prn_option())
                    else:
                        # assume it's an iterable
                        cmd.extend(option)

            if debug:
                if type(debug) == bool:
                    # assume debug level is 3
                    cmd.append("--nco_dbg_lvl=3")
                elif type(debug) == int:
                    cmd.append("--nco_dbg_lvl={0}".format(debug))
                else:
                    raise TypeError(
                        "Unknown type for debug: {0}".format(type(debug))
                    )

            if output and force and os.path.isfile(output):
                # make sure overwrite is set
                if debug:
                    print("Overwriting file: {0}".format(output))
                if any([i for i in cmd if i in self.DontForcePattern]):
                    force = False
            else:
                force = False

            # 2b. all other keyword args become options
            if kwargs:
                for key, val in list(kwargs.items()):
                    if val and type(val) == bool:
                        cmd.append("--{0}".format(key))
                        if cmd[-1] in self.DontForcePattern:
                            force = False
                    elif (
                        isinstance(val, str)
                        or isinstance(val, int)
                        or isinstance(val, float)
                    ):
                        cmd.append("--{option}={value}".format(option=key, value=val))
                    else:
                        # we assume it's either a list, a tuple or any iterable
                        cmd.append(
                            "--{option}={values}".format(
                                option=key, values=",".join(val)
                            )
                        )

            # 2c. Global options come in
            if self.options:
                for key, val in list(self.options.items()):
                    if val and type(val) == bool:
                        cmd.append("--" + key)
                    elif isinstance(val, str):
                        cmd.append("--{0}={1}".format(key, val))
                    else:
                        # we assume it's either a list, a tuple or any iterable
                        cmd.append("--{0}={1}".format(key, ",".join(val)))

            # 3.  Add in overwrite if necessary
            if force:
                cmd.append("--overwrite")

            # Check if operator appends
            operator_appends = False
            for piece in cmd:
                if piece in self.AppendOperatorsPattern:
                    operator_appends = True

            # If operator appends and NCO version >= 4.3.7, remove -H -M -m
            # and their ancillaries from outputOperatorsPattern
            if operator_appends and nco_command == "ncks":
                nco_version = self.version()
                if parse_version(nco_version) >= parse_version("4.3.7"):
                    self.outputOperatorsPattern = [
                        "-r",
                        "--revision",
                        "--vrs",
                        "--version",
                    ]

            # Check if operator prints out
            for piece in cmd:
                if piece in self.outputOperatorsPattern:
                    operator_prints_out = True

            if operator_prints_out:
                retvals = self.call(cmd, inputs=input)
                self.returncode = retvals["returncode"]
                self.stdout = retvals["stdout"]
                self.stderr = retvals["stderr"]
                if not self.has_error(nco_command, input, cmd, retvals):
                    return retvals["stdout"]
                    # parsing can be done by 3rd party
                else:
                    if self.return_none_on_error:
                        return None
                    else:
                        raise NCOException(**retvals)
            else:
                if output is not None:
                    if isinstance(output, str):
                        cmd.append("--output={0}".format(output))
                    else:
                        # we assume it's an iterable.
                        if len(output) > 1:
                            raise TypeError(
                                "Only one output allowed, must be string or 1 "
                                "length iterable. Recieved output: {out} with "
                                "a type of {type}".format(
                                    out=output, type=type(output)
                                )
                            )
                        cmd.extend("--output={0}".format(output))

                elif not (nco_command in self.SingleFileOperatorsPattern):
                    # create a temporary file, use this as the output
                    file_name_prefix = (
                        nco_command + "_" + os.path.basename(input)
                    )
                    tmp_file = tempfile.NamedTemporaryFile(
                        mode="w+b",
                        prefix=file_name_prefix,
                        suffix=".tmp",
                        delete=False
                    )
                    output = tmp_file.name
                    cmd.append("--output={0}".format(output))

                retvals = self.call(
                    cmd, inputs=input, environment=environment, use_shell=use_shell
                )
                self.returncode = retvals["returncode"]
                self.stdout = retvals["stdout"]
                self.stderr = retvals["stderr"]
                if self.has_error(nco_command, input, cmd, retvals):
                    if self.return_none_on_error:
                        return None
                    else:
                        print(self.stdout)
                        print(self.stderr)
                        raise NCOException(**retvals)

            if return_array:
                return self.read_array(output, return_array)
            elif return_ma_array:
                return self.read_ma_array(output, return_ma_array)
            elif self.return_cdf or return_cdf:
                if not self.return_cdf:
                    self.load_cdf_module()
                    return self.read_cdf(output)
            else:
                return output

        # cache the method for later
        if self.debug:
            print("Found method: {0}".format(nco_command))
        setattr(self.__class__, nco_command, get)
        return get.__get__(self)

    def load_cdf_module(self):
        if self.cdf_module == "netcdf4":
            try:
                import netCDF4 as cdf

                self.cdf = cdf
            except Exception:
                raise ImportError(
                    "Could not load python-netcdf4 - try to "
                    "setting 'cdf_module='scipy'"
                )
        elif self.cdf_module == "scipy":
            try:
                import scipy.io.netcdf as cdf

                self.cdf = cdf
            except Exception:
                raise ImportError(
                    "Could not load scipy.io.netcdf - try to "
                    "setting 'cdf_module='netcdf4'"
                )
        else:
            raise ValueError(
                "Unknown value provided for cdf_module.  Valid "
                "values are 'scipy' and 'netcdf4'"
            )

    def set_return_array(self, value=True):
        self.returnCdf = value
        if value:
            self.load_cdf_module()

    def unset_return_array(self):
        self.set_return_array(False)

    def has_nco(self, path=None):
        if path is None:
            path = self.nco_path

        if os.path.isdir(path) and os.access(path, os.X_OK):
            return True
        else:
            return False

    def check_nco(self):
        if self.has_nco():
            call = [os.path.join(self.nco_path, "ncra"), "--version"]
            proc = subprocess.Popen(
                call, stderr=subprocess.PIPE, stdout=subprocess.PIPE
            )
            retvals = proc.communicate()
            print(retvals)

    def set_nco_path(self, value):
        self.nco_path = value

    def get_nco_path(self):
        return self.nco_path

    # ==================================================================
    # Additional operators:
    # ------------------------------------------------------------------
    @property
    def module_version(self):
        return "0.0.0"

    def version(self):
        # return NCO's version
        proc = subprocess.Popen(
            [os.path.join(self.nco_path, "ncra"), "--version"],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        ret = proc.communicate()
        ncra_help = ret[1]
        if isinstance(ncra_help, bytes):
            ncra_help = ncra_help.decode("utf-8")
        match = re.search(r"NCO netCDF Operators version (\d.*) ", ncra_help)
        # some versions write version information in quotation marks
        if not match:
            match = re.search(r'NCO netCDF Operators version "(\d.*)" ', ncra_help)
        return match.group(1).split(" ")[0]

    def read_cdf(self, infile):
        """Return a cdf handle created by the available cdf library.
        python-netcdf4 and scipy supported (default:scipy)"""
        if not self.return_cdf:
            self.load_cdf_module()

        if self.cdf_module == "scipy":
            # making it compatible to older scipy versions
            file_obj = self.cdf.netcdf_file(infile, mode="r")
        elif self.cdf_module == "netcdf4":
            file_obj = self.cdf.Dataset(infile)
        else:
            raise ImportError(
                "Could not import data \
                              from file {0}".format(
                    infile
                )
            )
        return file_obj

    def open_cdf(self, infile):
        """Return a cdf handle created by the available cdf library.
        python-netcdf4 and scipy suported (default:scipy)"""
        if not self.return_cdf:
            self.load_cdf_module()

        if self.cdf_module == "scipy":
            # making it compatible to older scipy versions
            print("Use scipy")
            file_obj = self.cdf.netcdf_file(infile, mode="r+")
        elif self.cdf_module == "netcdf4":
            print("Use netcdf4")
            file_obj = self.cdf.Dataset(infile, "r+")
        else:
            raise ImportError(
                "Could not import data \
                              from file: {0}".format(
                    infile
                )
            )

        return file_obj

    def read_array(self, infile, var_name):
        """Directly return a numpy array for a given variable name"""
        file_handle = self.read_cdf(infile)
        try:
            # return the data array
            return file_handle.variables[var_name][:]
        except KeyError:
            print("Cannot find variable: {0}".format(var_name))
            raise KeyError

    def read_ma_array(self, infile, var_name):
        """Create a masked array based on cdf's FillValue"""
        file_obj = self.read_cdf(infile)

        # .data is not backwards compatible to old scipy versions, [:] is
        data = file_obj.variables[var_name][:]

        # load numpy if available
        try:
            import numpy as np
        except Exception:
            raise ImportError("numpy is required to return masked arrays.")

        if hasattr(file_obj.variables[var_name], "_FillValue"):
            # return masked array
            fill_val = file_obj.variables[var_name]._FillValue
            retval = np.ma.masked_where(data == fill_val, data)
        else:
            # generate dummy mask which is always valid
            retval = np.ma.array(data)

        return retval


def auto_doc(tool, nco_self):
    """
    Generate the __doc__ string of the decorated function by
    retrieving the nco man page or help information.

    :param tool:
    :param nco_self:
    :return:
    """
    def get_doc(cmd):
        try:
            return nco_self.call(cmd).get("stdout", b"").decode("utf-8")
        except Exception:
            return ""

    def add_doc(func):
        doc = get_doc(["man", tool])
        if not doc:
            doc = get_doc([tool, "--help"])
        else:
            m = re.search(r"(?<=\n\n)\S", doc)
            if m:
                doc = doc[m.start():]
        func.__doc__ = doc
        func.__name__ = tool
        return func

    return add_doc
