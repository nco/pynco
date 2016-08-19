import os
import re
import sys
import numpy as np

DEBUG=1

# check mode
validModes = dict({
    'append': 'a',
    'create': 'c',
    'delete': 'd',
    'modify': 'm',
    'nappend': 'n',
    'overwrite': 'o'
})

# netCDF type names
netTypes = dict({
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
npTypes = dict({
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

npTypesNP = dict({
    'float32': np.float32 ,
    'float':   np.float32 ,
    'float64': np.float64,
    'double': np.float64,
    'int32'  : np.int32,
    'int16'  : np.int16,
    'str'    : str,
    'char'   : str,
    'string' : str,  
    'byte':    np.byte,
    'ubyte'  : np.ubyte,
    'int8'   : np.byte,
    'uint8'  : np.ubyte,
    'uint16':  np.uint16,
    'uint32':  np.uint32,
    'int64':   np.int64,
    'uint64':  np.uint64
})



__prog__ = os.path.splitext(os.path.basename(__file__))[0]


class atted(object):

    def __init__(self, mode='overwrite',attName="",varName="", Value=None,  sType=None,**kwargs):
    #def __init__(self, **kwargs):
        mode = kwargs.pop('mode', mode)
        attName = kwargs.pop('attName', attName)
        varName = kwargs.pop('varName', varName)
        Value = kwargs.pop('Value', Value)
        sType = kwargs.pop('sType',sType )

        
        if mode == None or not mode in validModes:
            raise Exception('{0}: mode "{1}" not found'.format("atted()","atted():",mode))

         
        if attName==None or len(attName)==0: 
            raise Exception ('{0}: attName zero length\n'.format("atted()"))


        # set member defaults 
        self.mode=mode
        self.attName=attName
        self.varName=varName 
        self.npType=None
        self.npValue=None    

        # dont bother about type & value
        if self.mode=="delete":
            return None
        
        # deal with string quirk 
        # if user specifies type 'string' or 'sng' with a single character string 
        # the the output type should be 'sng and NOT 'c'. To do this we put the single string
        # inside a list the the prnOptions() method treats it as it would a list of strings

        if type(Value) is str and ( sType == 'string' or sType == 'sng'):  
          Value=[Value]

        # see if Value is iterable   
        try:
            if type(Value) is str:
              raise TypeError("str is not iterable (for our purposes")
            it=iter(Value)    
            inputType=type(next(it))   
            bIterable=True
            del it   
        except Exception:
            bIterable=False 
            inputType=type(Value) 
         
         
        if sType:
            try:    
                npType=npTypesNP[sType] 
            except:
                raise Exception('{0}: specified Type "{1}" not found.\nValid values {2}\n'.format("atted()", sType, npTypes.keys()))                          
        # set default types
        else: 
           if inputType is int:
               npType=np.int32
           elif inputType is float:
               npType=np.float64
           elif inputType is str:
               npType=str
           # check the input type 
           else:  
               try: 
                      
                   x=npTypes[str(np.dtype(inputType)) ] 
                   npType=inputType
               except:
                   raise Exception('{0}: The type of Value "{1}" is NOT valid\nValid values {2}\n'.format("atted()", inputType, npTypes.keys()))                          

        if bIterable:                          
            npValue=list() 
            for v in Value:    
                npValue.append(np.dtype(npType).type(v))
        else:
            npValue=np.dtype(npType).type(Value) 
        
        if npValue:
          self.npType=npType
          self.npValue=npValue 
                        
    def __str__(self):
          return ('mode="{0}" attName="{1}" varName="{2} Value="{3}" type="{4}"\n'.format(self.mode, self.attName, self.varName, self.npValue, self.npType))
 
    def prnOption(self): 

              
        modeChar=validModes[self.mode]

        # deal with delete - nb doesnt need any data 
        if self.mode=='delete':  
            return ('-a "{0}","{1}",{2},,'.format(self.attName,self.varName, modeChar))   

        bList= type(self.npValue) is list        
  
        # deal with string quirks here 
        if self.npType is str:
           if bList:
             typeChar="sng"
           else:
             typeChar="c"
        else:
           npTypeStr=str(np.dtype(self.npType)) 
           typeChar=npTypes[npTypeStr]    


        # deal with a single value first   
        if not bList:
           self.npValue=[self.npValue]

        if self.npType is str:          
            strArray=['"'+str(v)+'"'  for v in self.npValue]
        else: 
            strArray=[str(v)  for v in self.npValue]

        strValue=",".join(strArray)

       
        return ('-a "{0}","{1}",{2},{3},{4}'.format(self.attName,self.varName, modeChar, typeChar, strValue))  
           

################# main ################################

def test():
     
    a1=atted(mode="overwrite", attName="units", varName="temperature", Value="Kelvin")
    a2=atted(mode="overwrite", attName="min", varName="temperature", Value=-127 ,sType='byte' )
    a3=atted(mode="overwrite", attName="max", varName="temperature", Value=127, sType='int16')
    a4=atted(mode="modify", attName="min-max", varName="pressure", Value=[100,10000], sType='int32')
    a5=atted(mode="create", attName="array", varName="time_bands", Value=range(1,10,2), sType='float')
    a6=atted(mode="append", attName="mean", varName="time_bands", Value=3.14159826253) #default to double
    a6=atted(mode="append", attName="mean_float", varName="time_bands", Value=3.14159826253, sType='float' ) #d convert type to float
    a7=atted(mode="append", attName="mean_sng", varName="time_bands", Value=3.14159826253,sType='char')
    a8=atted(mode="nappend", attName="units", varName="height", Value="height in mm", sType='string')
    

    # regular function args
    a9=atted("append", "long_name", "temperature", ("mean", "sea","level","temperature"))
    a10=atted("delete", "short_name", "temp")
    a11=atted("delete","long_name","relative_humidity")

    ar=("mean", "sea","level","temperature",3.1459,2.0)
    a11=atted("append", "long_name", "temperature", ar)

    a12=atted(mode="delete", attName=".*")

    val=np.dtype(np.complex).type(123456.0)
    a13=atted(mode="append", attName="array", varName="time", Value=val,sType='int64')


    # a1.prn()
    print a2.prnOption()
    print a3.prnOption()
    print a4.prnOption()
    print a5.prnOption()
    print a6.prnOption()
    print a7.prnOption()
    print a8.prnOption()
    print a9.prnOption()
    print str(a10)
    print str(a11)
    print str(a12)
    print str(a13)
                  
  

test()
