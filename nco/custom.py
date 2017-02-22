"""
custom module:
This is an extension to the nco module
It contains wrappers to the most common NCO command line switches.
This makes it more easy for users to specify strings and literals

Atted - wrapper for -a swtch in ncatted
Limit/LimtSingle - wrapper to -d switch
Rename - wrapper for -a, -v, -d, -g switches in ncrename
"""

import os
import numpy as np

DEBUG = 1

# valid values for rename type
RENAME_TYPES = dict({
    'attribute': 'a',
    'dimension': 'd',
    'group': 'g',
    'variable': 'v'
})

# check mode
VALID_MODES = dict({
    'create': 'c',
    'delete': 'd',
    'modify': 'm',
    'append': 'a',
    'nappend': 'n',
    'overwrite': 'o'
})

# netCDF type names
NET_TYPES = dict({
    'NC_FLOAT': 'f',
    'NC_DOUBLE': 'd',
    'NC_INT': 'i',
    'NC_SHORT': 's',
    'NC_CHAR': 'c',
    'NC_BYTE': 'b',
    'NC_UBYTE': 'ub',
    'NC_USHORT': 'us',
    'NC_UINT': 'ui',
    'NC_INT64': 'll',
    'NC_UINT64': 'ull',
    'NC_STRING': 'sng'
})

# numpy type names
NP_TYPES = dict({
    'float32': 'f',
    'float64': 'd',
    'int32': 'i',
    'int16': 's',
    'char': 'c',
    'byte': 'b',
    'ubyte': 'ub',
    'int8': 'b',
    'uint8': 'ub',
    'uint16': 'us',
    'uint32': 'ui',
    'int64': 'll',
    'uint64': 'ull',
    'string': 'sng'
})

NP_TYPESNP = dict({
    'float32': np.float32,
    'float': np.float32,
    'f': np.float32,
    'float64': np.float64,
    'double': np.float64,
    'd': np.float64,
    'int32': np.int32,
    'i': np.int32,
    'l': np.int32,
    'int16': np.int16,
    's': np.int16,
    'str': str,
    'char': str,
    'c': str,
    'string': str,
    'sng': str,
    'byte': np.byte,
    'b': np.byte,
    'ubyte': np.ubyte,
    'ub': np.ubyte,
    'int8': np.byte,
    'uint8': np.ubyte,
    'uint16': np.uint16,
    'us': np.uint16,
    'uint32': np.uint32,
    'u': np.uint32,
    'ui': np.uint32,
    'ul': np.uint32,
    'int64': np.int64,
    'll': np.int64,
    'uint64': np.uint64,
    'ull': np.uint64
})

__prog__ = os.path.splitext(os.path.basename(__file__))[0]


class Atted(object):
    """
    wrapper to -a ncatted command line switch
     command line swtich looks like

     -a,att_nm,var_nm,mode,att_typ,att_val
     mode = a,c,d,m,o,n (append, create, delete, modify, overwrite, nappend)
     att_typ = f,d,l/i,s,c,b,ub,us,u,ll,ull,sng
     """

    def __init__(self, mode='overwrite', att_name="", var_name="", value=None,
                 stype=None, **kwargs):
        mode = kwargs.pop('mode', mode)
        att_name = kwargs.pop('att_name', att_name)
        var_name = kwargs.pop('var_name', var_name)
        value = kwargs.pop('value', value)
        stype = kwargs.pop('stype', stype)

        if mode in VALID_MODES:
            mode = VALID_MODES[mode]
        elif mode in VALID_MODES.values():
            pass
        else:
            raise KeyError('mode "{0}" not found'.format(mode))

        if not att_name:
            raise ValueError('att_name is required')

        # set member defaults
        self.mode = mode
        self.att_name = att_name
        self.var_name = var_name
        self.np_type = None
        self.np_value = None

        # dont bother about type & value
        if self.mode == "d":
            return

        # deal with string quirk
        # if user specifies type 'string' or 'sng' with a single character
        # string the the output type should be 'sng and NOT 'c'. To do this we
        # put the single string inside a list the the prnOptions() method
        # treats it as it would a list of strings
        if isinstance(value, str) and stype in ['string', 'sng']:
            value = [value]

        # see if value is iterable
        try:
            if isinstance(value, str):
                raise TypeError("str is not iterable (for our purposes")
            it = iter(value)
            input_type = type(next(it))
            biterable = True
        # catch if value is str or  no __iter__  in value
        except TypeError:
            biterable = False
            input_type = type(value)

        if stype:
            try:
                np_type = NP_TYPESNP[stype]
            except:
                raise KeyError('specified Type "{0}" not found.\nValid '
                               'values {1}\n'.format(stype, NP_TYPES.keys()))
        # set default types
        else:
            if input_type is int:
                np_type = np.int32
            elif input_type is float:
                np_type = np.float64
            elif input_type is str:
                np_type = str
            # check the input type
            else:
                try:
                    NP_TYPES[str(np.dtype(input_type))]
                    np_type = input_type
                except KeyError:
                    raise KeyError(
                        'The type of value "{0}" is NOT valid\nValid '
                        'values {1}\n'.format(input_type, NP_TYPES.keys()))

        if biterable:
            if np_type is str:
                # convert everything to string
                sList = [np.dtype(str).type(v) for v in value]

                # get max string length
                lenMax = len(max(sList, key=len))
                # create array of 'fixed' length strings
                np_value = np.array(sList, 'S{0}'.format(lenMax))
            else:
                # create array from iterable all in one go !!
                np_value = np.fromiter(value, np_type)
        else:
            np_value = np.dtype(np_type).type(value)

        if np_value is not None:
            self.np_type = np_type
            self.np_value = np_value

    def __str__(self):
        return ('mode="{0}" att_name="{1}" var_name="{2} value="{3}" '
                'type="{4}"\n'.format(self.mode, self.att_name, self.var_name,
                                      self.np_value, self.np_type))

    def prn_option(self):

        # modeChar=VALID_MODES[self.mode]
        # deal with delete - nb doesnt need any data
        if self.mode == 'd':
            return ('-a "{0}","{1}",{2},,'.
                    format(self.att_name, self.var_name, self.mode))

        bList = isinstance(self.np_value, (list, np.ndarray))

        # deal with string quirks here
        # if isinstance(self.np_type, str):
        if self.np_type is str:
            if bList:
                type_char = "sng"
            else:
                type_char = "c"
        else:
            nptype_str = str(np.dtype(self.np_type))
            type_char = NP_TYPES[nptype_str]

        # deal with a single value first
        if not bList:
            self.np_value = [self.np_value]

        # if isinstance(self.np_type, str):
        if self.np_type is str:
            strArray = ['"' + str(v) + '"' for v in self.np_value]
        else:
            strArray = [str(v) for v in self.np_value]

        strvalue = ",".join(strArray)

        return '-a "{0}","{1}",{2},{3},{4}'.format(self.att_name,
                                                   self.var_name,
                                                   self.mode,
                                                   type_char,
                                                   strvalue)


class Limit(object):
    """
    wrapper to the NCO command-line hyperslab option
    format of  -d switch -d dmn_name,min,max,stride,subcycle
    the dmn_name is mandatory all the other parameters are optional
    but at least one must be specified for a valid hyperslab
    """

    def __init__(self, dmn_name="", srt="", end="", srd="", drn="", **kwargs):

        dmn_name = kwargs.pop('dmn_name', dmn_name)
        srt = kwargs.pop('srt', srt)
        end = kwargs.pop('end', end)
        srd = kwargs.pop('srd', srd)
        drn = kwargs.pop('drn', drn)

        if not dmn_name:
            raise ValueError('dmn_name is required')

        self.dmn_name = dmn_name
        # set rest of defaults
        self.srt = ""
        self.end = ""
        self.srd = ""
        self.drn = ""

        if srt != "":
            if isinstance(srt, float):
                self.srt = srt
            else:
                # convert index to long long
                self.srt = np.dtype(np.int64).type(srt)
        if end != "":
            if isinstance(end, float):
                self.end = end
            else:
                # convert index to long long
                self.end = np.dtype(np.int64).type(end)

        if srd != "":
            self.srd = np.dtype(np.int64).type(srd)

        if drn != "":
            self.drn = np.dtype(np.int64).type(drn)

    def __str__(self):
        return ("dmn_name={} srt={} end={} srd={} drn={}".
                format(self.dmn_name, self.srt, self.end, self.srd, self.drn))

    def prn_option(self):
        bstr = '-d "{0}",{1},{2}'.format(self.dmn_name, self.srt, self.end)

        if self.drn != "":
            estr = ",{0},{1}".format(self.srd, self.drn)
        elif self.srd != "":
            estr = ",{0}".format(self.srd)
        else:
            estr = ""

        bstr += estr

        return bstr


class LimitSingle(Limit):
    """
    limitsingle is where user request a single limit and not a range - on the
    command line this looks like:
    eg "-d lon,10"  and NOT  "-d lon,10,"
    (the comma signfies a range to default end)
    """

    def __init__(self, dmn_name="", srt="", end="", srd="", drn="", **kwargs):
        if srt == "":
            raise Exception('must specify "srt"')

        Limit.__init__(self, dmn_name, srt, end, srd, drn, **kwargs)

    def prn_option(self):
        """
        Override of the base method in Limit.
        This just prints the "srt" index
        """
        bstr = '-d "{0}",{1}'.format(self.dmn_name, self.srt)

        return bstr


class Rename(object):
    """
     wrapper for the ncrename operator
     command-line format
         rename attribute -a old_att_nm, new_att_nm
         rename variable  -v old_var_nm, new_var_nm
         rename dimension -d old_nm_nm,  new_dmn_nm
         rename groupg    -g old_grp_nm, new_grp_nm

      rtype specifies the object to rename -
      rdict: a user defined dictionary - mapping old_nm _>new_nm
    """

    def __init__(self, rtype, rdict):

        if rtype in RENAME_TYPES.keys():
            rtype = RENAME_TYPES[rtype]
        elif rtype in RENAME_TYPES.values():
            pass
        else:
            raise KeyError('rtype "{0}" not found'.format(rtype))

        self.rtype = rtype
        self.rDict = rdict

    def prn_option(self):

        lout = []
        for (sKey, Value) in self.rDict.items():
            sf = '-{0} "{1}","{2}"'.format(self.rtype, sKey, Value)
            lout.append(sf)

        sout = " ".join(lout)
        return sout
