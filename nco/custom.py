import os
import re
import sys
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
    'append': 'a',
    'create': 'c',
    'delete': 'd',
    'modify': 'm',
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


# wrapper to -a ncatted command line switch
# command line swtich looks like
#
# -a,att_nm,var_nm,mode,att_typ,att_val
# mode = a,c,d,m,o,n (append, create, delete, modify, overwrite, nappend)
# att_typ = f,d,l/i,s,c,b,ub,us,u,ll,ull,sng
class atted(object):
    def __init__(self, mode='overwrite', att_name="", var_name="", value=None, stype=None, **kwargs):
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
            raise Exception('mode "{0}" not found'.format(mode))

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
        # if user specifies type 'string' or 'sng' with a single character string 
        # the the output type should be 'sng and NOT 'c'. To do this we put the single string
        # inside a list the the prnOptions() method treats it as it would a list of strings
        if isinstance(value, str) and stype in ['string', 'sng']:
            value = [value]

        # see if value is iterable   
        try:
            if isinstance(value, str):
                raise TypeError("str is not iterable (for our purposes")
            it = iter(value)
            inputType = type(next(it))
            bIterable = True
        except Exception:
            bIterable = False
            inputType = type(value)

        if stype:
            try:
                np_type = NP_TYPESNP[stype]
            except:
                raise Exception('specified Type "{0}" not found.\nValid values {1}\n'.format(stype, NP_TYPES.keys()))
        # set default types
        else:
            if inputType is int:
                np_type = np.int32
            elif inputType is float:
                np_type = np.float64
            elif inputType is str:
                np_type = str
            # check the input type
            else:
                try:
                    x = NP_TYPES[str(np.dtype(inputType))]
                    np_type = inputType
                except:
                    raise Exception(
                        'The type of value "{0}" is NOT valid\nValid values {1}\n'.format(inputType, NP_TYPES.keys()))

        if bIterable:
            if np_type is str:
                # convert everything to string
                sList = [np.dtype(str).type(v) for v in value]

                # get max string length
                lenMax = len(max(sList, key=len))
                # create array of 'fixed' length strings
                np_value = np.array(sList, 'S{0}'.format(lenMax))
            else:
                np_value = np.fromiter(value, np_type)  # create array from iterable all in one go !!
        else:
            np_value = np.dtype(np_type).type(value)

        if np_value is not None:
            self.np_type = np_type
            self.np_value = np_value

    def __str__(self):
        return ('mode="{0}" att_name="{1}" var_name="{2} value="{3}" type="{4}"\n'.format(self.mode, self.att_name,
                                                                                          self.var_name, self.np_value,
                                                                                          self.np_type))

    def prnOption(self):

        # modeChar=VALID_MODES[self.mode]
        # deal with delete - nb doesnt need any data 
        if self.mode == 'd':
            return ('-a "{0}","{1}",{2},,'.format(self.att_name, self.var_name, self.mode))

        bList = isinstance(self.np_value, (list, np.ndarray))

        # deal with string quirks here 
        # if isinstance(self.np_type, str):
        if self.np_type is str:
            if bList:
                typeChar = "sng"
            else:
                typeChar = "c"
        else:
            npTypeStr = str(np.dtype(self.np_type))
            typeChar = NP_TYPES[npTypeStr]

        # deal with a single value first
        if not bList:
            self.np_value = [self.np_value]

        # if isinstance(self.np_type, str):
        if self.np_type is str:
            strArray = ['"' + str(v) + '"' for v in self.np_value]
        else:
            strArray = [str(v) for v in self.np_value]

        strvalue = ",".join(strArray)

        return ('-a "{0}","{1}",{2},{3},{4}'.format(self.att_name, self.var_name, self.mode, typeChar, strvalue))


# wrapper to the NCO command-line hyperslab option
# format of  -d switch -d dmn_name,min,max,stride,subcycle
# the dmn_name is mandatory all the other parameters are optional
# but at least one must be specified for a valid hyperslab
class limit(object):
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
        return ("dmn_name={} srt={} end={} srd={} drn={}".format(self.dmn_name, self.srt, self.end, self.srd, self.drn))

    def prnOption(self):
        bstr = '-d "{0}",{1},{2}'.format(self.dmn_name, self.srt, self.end)

        if self.drn != "":
            estr = ",{0},{1}".format(self.srd, self.drn)
        elif self.srd != "":
            estr = ",{0}".format(self.srd)
        else:
            estr = ""

        bstr += estr

        return bstr


# limitsingle is where user request a single limit and not a range - on the command line this looks like:
#  eg "-d lon,10"  and NOT  "-d lon,10," (the comma signfies range to default end)
#  the base method prnOption() has been overrided so that it just prints srt
class limitsingle(limit):
    def __init__(self, dmn_name="", srt="", end="", srd="", drn="", **kwargs):
        if srt == "":
            raise Exception('must specify "srt"')

        limit.__init__(self, dmn_name, srt, end, srd, drn, **kwargs)

    def prnOption(self):
        bstr = '-d "{0}",{1}'.format(self.dmn_name, self.srt)

        return bstr


# wrapper for the ncrename operator
# command-line format
#     rename attribute -a old_att_nm, new_att_nm
#     rename variable  -v old_var_nm, new_var_nm
#     rename dimension -d old_nm_nm,  new_dmn_nm
#     rename groupg    -g old_grp_nm, new_grp_nm
#
#  rtype specifies the object to rename -
#  rdict: a user defined dictionary - mapping old_nm _>new_nm
class rename(object):
    def __init__(self, rtype, rdict):

        if rtype in RENAME_TYPES.keys():
            rtype = RENAME_TYPES[rtype]
        elif rtype in RENAME_TYPES.values():
            pass
        else:
            raise Exception('rtype "{0}" not found'.format(rtype))

        self.rtype = rtype
        self.rDict = rdict

    def prnOption(self):

        lout = []
        for (sKey, Value) in self.rDict.items():
            sf = '-{0} "{1}","{2}"'.format(self.rtype, sKey, Value)
            lout.append(sf)

        sout = " ".join(lout)
        return sout


################# myTest ################################
def mytest():
    AttedList = [
        atted(mode="overwrite", att_name="units", var_name="temperature", value="Kelvin"),
        atted(mode="overwrite", att_name="min", var_name="temperature", value=-127, stype='byte'),
        atted(mode="overwrite", att_name="max", var_name="temperature", value=127, stype='int16'),
        atted(mode="modify", att_name="min-max", var_name="pressure", value=[100, 10000], stype='int32'),
        atted(mode="create", att_name="array", var_name="time_bands", value=range(1, 10, 2), stype='d'),
        atted(mode="append", att_name="mean", var_name="time_bands", value=3.14159826253),  # default to double
        atted(mode="append", att_name="mean_float", var_name="time_bands", value=3.14159826253, stype='float'),
        # d convert type to float
        atted(mode="append", att_name="mean_sng", var_name="time_bands", value=3.14159826253, stype='char'),
        atted(mode="nappend", att_name="units", var_name="height", value="height in mm", stype='string'),
        atted(mode="create", att_name="long_name", var_name="height", value="height in feet"),
        atted(mode="nappend", att_name="units", var_name="blob", value=[1000000., 2.], stype='d')
    ]

    # regular function args
    AttedList += [
        atted("append", "long_name", "temperature", ("mean", "sea", "level", "temperature")),
        atted("delete", "short_name", "temp"),
        atted("delete", "long_name", "relative_humidity")
    ]

    ar = ("mean", "sea", "level", "temperature", 3.1459, 2.0)
    val = np.dtype(np.complex).type(123456.0)
    val2 = np.dtype(np.bool).type(False)

    # val=10.0

    AttedList += [
        atted("append", "long_name", "temperature", ar),
        atted(mode="delete", att_name=".*"),
        atted(mode="append", att_name="array", var_name="time", value=val, stype='ll'),
        atted(mode="append", att_name="bool", var_name="time", value=val2, stype='b'),
        atted("nappend", "long", "random", 2 ** 33, stype='ull')
    ]

    for a in AttedList:
        print a.prnOption()

    LimitList = [limit("lat", 0.0, 88.1),
                 limit("time", 0, 10, 3),
                 limit("time", 1.0, 2e9, 3),
                 limit(dmn_name="three", srt=10, end=30, srd=4, drn=2),
                 limit(dmn_name="three", srd=4),
                 limit(dmn_name="three", drn=3),
                 limitsingle("three", 20.0)
                 ]

    for l in LimitList:
        print l.prnOption()

    tstrename = dict({'lon': 'longitude', 'lat': 'latitude', 'lev': 'level', 'dog': 'cat'})
    myrename = rename("g", tstrename)
    print myrename.prnOption()


################# main ######################################################

#mytest()
