import os
import re
import sys
import numpy as np

DEBUG=1

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
    'int8' : 'b',
    'uint8' : 'ub',
    'uint16': 'us',
    'uint32': 'ui',
    'int64': 'll',
    'uint64': 'ull',
    'string': 'sng'
})

NP_TYPESNP = dict({
    'float32' : np.float32, 
    'float'   : np.float32 ,
    'f'       : np.float32 ,
    'float64' : np.float64,
    'double'  : np.float64,
    'd'       : np.float64,
    'int32'   : np.int32,
    'i'       : np.int32,
    'l'       : np.int32,
    'int16'   : np.int16,
    's'       : np.int16,
    'str'     : str,
    'char'    : str,
    'c'       : str,
    'string'  : str,  
    'sng'     : str,  
    'byte'    : np.byte,
    'b'       : np.byte,
    'ubyte'   : np.ubyte,
    'ub'      : np.ubyte,
    'int8'    : np.byte,
    'uint8'   : np.ubyte,
    'uint16'  : np.uint16,
    'us'      : np.uint16,
    'uint32'  : np.uint32,
    'u'       : np.uint32,
    'ui'      : np.uint32,
    'ul'      : np.uint32,
    'int64'   : np.int64,
    'll'      : np.int64,
    'uint64'  : np.uint64,
    'ull'     : np.uint64
})


__prog__ = os.path.splitext(os.path.basename(__file__))[0]


class atted(object):

    def __init__(self, mode='overwrite',att_name="",var_name="", value=None,  stype=None,**kwargs):
        mode = kwargs.pop('mode', mode)
        att_name = kwargs.pop('att_name', att_name)
        var_name = kwargs.pop('var_name', var_name)
        value = kwargs.pop('value', value)
        stype = kwargs.pop('stype',stype )
            
        if mode in VALID_MODES:
           mode=VALID_MODES[mode]  
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
            it=iter(value)    
            inputType=type(next(it))   
            bIterable=True
        except Exception:
            bIterable=False 
            inputType=type(value) 
         
         
        if stype:
            try:    
                np_type=NP_TYPESNP[stype]
            except:
                raise Exception('specified Type "{0}" not found.\nValid values {1}\n'.format(stype, NP_TYPES.keys()))
        # set default types
        else: 
           if inputType is int:
               np_type=np.int32
           elif inputType is float:
               np_type=np.float64
           elif inputType is str:
               np_type=str
           # check the input type 
           else:  
               try: 
                   x=NP_TYPES[str(np.dtype(inputType)) ]
                   np_type=inputType
               except:
                   raise Exception('The type of value "{0}" is NOT valid\nValid values {1}\n'.format(inputType, NP_TYPES.keys()))

        if bIterable:              
            if np_type is str:
                # convert everything to string
                sList=[np.dtype(str).type(v) for v in value]
               
                # get max string length
                lenMax=len(max(sList,key=len))
                # create array of 'fixed' length strings
                np_value=np.array(sList , 'S{0}'.format(lenMax))
            else:
                np_value=np.fromiter(value, np_type)  # create array from iterable all in one go !!
        else:
            np_value=np.dtype(np_type).type(value)


        if np_value is not None:
          self.np_type = np_type
          self.np_value = np_value
                        
    def __str__(self):
          return ('mode="{0}" att_name="{1}" var_name="{2} value="{3}" type="{4}"\n'.format(self.mode, self.att_name, self.var_name, self.np_value, self.np_type))

    def prnOption(self): 

              
        # modeChar=VALID_MODES[self.mode]
        # deal with delete - nb doesnt need any data 
        if self.mode == 'd':
            return ('-a "{0}","{1}",{2},,'.format(self.att_name,self.var_name, self.mode))   

        bList = isinstance(self.np_value, (list, np.ndarray))

        # deal with string quirks here 
        # if isinstance(self.np_type, str):
        if self.np_type is str:
           if bList:
             typeChar = "sng"
           else:
             typeChar = "c"
        else:
           npTypeStr=str(np.dtype(self.np_type))
           typeChar=NP_TYPES[npTypeStr]


        # deal with a single value first   
        if not bList:
           self.np_value = [self.np_value]

        # if isinstance(self.np_type, str):
        if self.np_type is str:
            strArray=['"'+str(v)+'"'  for v in self.np_value]
        else: 
            strArray=[str(v)  for v in self.np_value]


        strvalue=",".join(strArray)

       
        return ('-a "{0}","{1}",{2},{3},{4}'.format(self.att_name,self.var_name, self.mode, typeChar, strvalue))  
           

################# main ################################

def test():
     
    AttedList=[ 
      atted(mode="overwrite", att_name="units", var_name="temperature", value="Kelvin"),
      atted(mode="overwrite", att_name="min", var_name="temperature", value=-127 ,stype='byte' ),
      atted(mode="overwrite", att_name="max", var_name="temperature", value=127, stype='int16'),
      atted(mode="modify", att_name="min-max", var_name="pressure", value=[100,10000], stype='int32'),
      atted(mode="create", att_name="array", var_name="time_bands", value=range(1,10,2), stype='d'),
      atted(mode="append", att_name="mean", var_name="time_bands", value=3.14159826253), #default to double
      atted(mode="append", att_name="mean_float", var_name="time_bands", value=3.14159826253, stype='float' ), #d convert type to float
      atted(mode="append", att_name="mean_sng", var_name="time_bands", value=3.14159826253,stype='char'),
      atted(mode="nappend", att_name="units", var_name="height", value="height in mm", stype='string'),
      atted(mode="create", att_name="long_name", var_name="height", value="height in feet"),
      atted(mode="nappend", att_name="units", var_name="blob", value=[1000000.,2.], stype='d')
    ]  

    # regular function args
    AttedList+=[
       atted("append", "long_name", "temperature", ("mean", "sea","level","temperature")),
       atted("delete", "short_name", "temp"),
       atted("delete","long_name","relative_humidity")
    ]   

    ar=("mean", "sea","level","temperature",3.1459,2.0)
    val=np.dtype(np.complex).type(123456.0)
    val2=np.dtype(np.bool).type(False)

    # val=10.0

    AttedList+=[ 
       atted("append", "long_name", "temperature", ar),
       atted(mode="delete", att_name=".*"),
       atted(mode="append", att_name="array", var_name="time", value=val,stype='ll'),
       atted(mode="append", att_name="bool", var_name="time", value=val2,stype='b'),
       atted("nappend", "long", "random", 2**33, stype='ull')     
    ]

   
    for a in AttedList:
      print str(a)
      print a.prnOption()

# test()
