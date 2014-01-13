import os, re, subprocess, tempfile, random, string



def auto_doc(tool, nco_self):
    """Generate the __doc__ string of the decorated function by calling the nco help command"""
    def desc(func):
        func.__doc__ = nco_self.call([nco_self.NCO, '-h', tool]).get('stdout')
        return func
    return desc

class NCOException(Exception):

    def __init__(self, stdout, stderr, returncode):
        super(NCOException, self).__init__()
        self.stdout     = stdout
        self.stderr     = stderr
        self.returncode = returncode
        self.msg        = '(returncode:%s) %s' % (returncode, stderr)

    def __str__(self):
        return self.msg

class Nco(object):

  def __init__(self, returnCdf=False, returnNoneOnError=False, forceOutput=True, cdfMod='scipy', debug=False):

    operators = ['ncap2', 'ncatted', 'ncbo', 'nces', 'ncecat', 'ncflint', 'ncks',
                 'ncpdq', 'ncra', 'ncrcat', 'ncrename', 'ncwa']

    if os.environ.has_key('NCO'):
      self.NCO = os.environ['NCO']
    else:
      self.NCO = 'nco'

    self.operators              = operators
    self.returnCdf              = returnCdf
    self.returnNoneOnError      = returnNoneOnError
    self.tempfile               = MyTempfile()
    self.forceOutput            = forceOutput
    self.cdfMod                 = cdfMod
    self.debug                  = debug
    self.outputOperatorsPattern = '(diff|info|output|griddes|zaxisdes|show|ncode|ndate|nlevel|nmon|nvar|nyear|ntime|npar|gradsdes|pardes)'

  def __dir__(self):
    res = dir(type(self)) + list(self.__dict__.keys())
    res.extend(self.operators)
    return res

  def call(self, cmd, environment=None):
    if self.debug:
      print '# DEBUG ====================================================================='
      if None != environment:
        for k,v in environment.items():
          print "ENV: " + k + " = " + v
      print 'CALL:'+' '.join(cmd)
      print '# DEBUG ====================================================================='

    proc = subprocess.Popen(' '.join(cmd),
                            shell  = True,
                            stderr = subprocess.PIPE,
                            stdout = subprocess.PIPE,
                            env    = environment)
    retvals = proc.communicate()
    return {"stdout"     : retvals[0]
           ,"stderr"     : retvals[1]
           ,"returncode" : proc.returncode}

  def hasError(self, method_name, cmd, retvals):
    if (self.debug):
      print("RETURNCODE:"+retvals["returncode"].__str__())
    if ( 0 != retvals["returncode"] ):
      print("Error in calling operator " + method_name + " with:")
      print(">>> "+' '.join(cmd)+"<<<")
      print(retvals["stderr"])
      return True
    else:
      return False

  def __getattr__(self, method_name):

    @auto_doc(method_name, self)
    def get(self, *args, **kwargs):
      operator          = [method_name]
      operatorPrintsOut = False

      if args.__len__() != 0:
        for arg in args:
          operator.append(arg.__str__())

      #build the nco command
      #1. the nco command
      cmd = [self.NCO]
      #2. options
      if 'options' in kwargs:
          cmd += kwargs['options'].split()
      #3. operator(s)
      cmd.append(','.join(operator))
      #4. input files or operators
      if 'input' in kwargs:
        if isinstance(kwargs["input"], basestring):
            cmd.append(kwargs["input"])
        else:
            #we assume it's either a list, a tuple or any iterable.
            cmd += kwargs["input"]

      if not kwargs.__contains__("force"):
        kwargs["force"] = self.forceOutput

      if operatorPrintsOut:
        retvals = self.call(cmd)
        if ( not self.hasError(method_name, cmd, retvals) ):
          r = map(string.strip,retvals["stdout"].split(os.linesep))
          return r[:len(r)-1]
        else:
          if self.returnNoneOnError:
            return None
          else:
            raise NCOException(**retvals)
      else:
        if kwargs["force"] or \
           (kwargs.__contains__("output") and not os.path.isfile(kwargs["output"])):
          if not kwargs.__contains__("output") or None == kwargs["output"]:
            kwargs["output"] = self.tempfile.path()

          cmd.append(kwargs["output"])
          if kwargs.__contains__("env"):
            environment = kwargs["env"]
          else:
            environment = None

          retvals = self.call(cmd, environment=environment)
          if self.hasError(method_name,cmd, retvals):
            if self.returnNoneOnError:
              return None
            else:
              raise NCOException(**retvals)
        else:
          if self.debug:
            print("Use existing file'"+kwargs["output"]+"'")

      if not kwargs.__contains__("returnCdf"):
        kwargs["returnCdf"] = False

      if not None == kwargs.get("returnArray"):
        return self.readArray(kwargs["output"], kwargs["returnArray"])
      elif not None == kwargs.get("returnMaArray"):
        return self.readMaArray(kwargs["output"], kwargs["returnMaArray"])
      elif self.returnCdf or kwargs["returnCdf"]:
        if not self.returnCdf:
          self.loadCdf()
        return self.readCdf(kwargs["output"])
      else:
        return kwargs["output"]

    if ((method_name in self.__dict__) or (method_name in self.operators)):
      if self.debug:
        print("Found method:" + method_name)

      #cache the method for later
      setattr(self.__class__, method_name, get)
      return get.__get__(self)
    else:
      # If the method isn't in our dictionary, act normal.
      print("#=====================================================")
      print("Cannot find method:" + method_name)
      raise AttributeError, "Unknown method '" + method_name +"'!"

  def loadCdf(self):
    if self.cdfMod == "scipy":
      try:
        import scipy.io.netcdf as cdf
        self.cdf    = cdf
      except:
        print "Could not load scipy.io.netcdf - try to load nercdf4"
        self.cdfMod = "netcdf4"

    if self.cdfMod == "netcdf4":
      try:
        import netCDF4 as cdf
        self.cdf    = cdf
      except:
        raise ImportError,"scipy or python-netcdf4 module is required to return numpy arrays."

  def setReturnArray(self, value=True):
    self.returnCdf = value
    if value:
      self.loadCdf()


  def unsetReturnArray(self):
    self.setReturnArray(False)

  def hasNco(self, path=None):
    if path is None:
      path = self.NCO

    if os.path.isfile(path) and os.access(path, os.X_OK):
      return True
    return False

  def checkNco(self):
    if (self.hasNco()):
      call = [self.NCO,' -V']
      proc = subprocess.Popen(' '.join(call),
          shell  = True,
          stderr = subprocess.PIPE,
          stdout = subprocess.PIPE)
      retvals = proc.communicate()
      print retvals

  def setNco(self, value):
    self.NCO       = value

  def getNco(self):
    return self.NCO


  #==================================================================
  # Addional operators:
  #------------------------------------------------------------------
  def module_version(self):
    return '1.2.3'

  def version(self):
    # return NCO's version
    proc = subprocess.Popen([self.NCO,'-h'],stderr = subprocess.PIPE,stdout = subprocess.PIPE)
    ret  = proc.communicate()
    nco_help   = ret[1]
    match = re.search("NCO version (\d.*), Copyright",nco_help)
    return match.group(1)

  def boundaryLevels(self,**kwargs):
    ilevels         = map(float,self.showlevel(input = kwargs['input'])[0].split())
    bound_levels    = []
    bound_levels.insert(0,0)
    for i in range(1,len(ilevels)+1):
      bound_levels.insert(i,bound_levels[i-1] + 2*(ilevels[i-1]-bound_levels[i-1]))

    return bound_levels

  def thicknessOfLevels(self,**kwargs):
    bound_levels = self.boundaryLevels(**kwargs)
    delta_levels    = []
    for i in range(0,len(bound_levels)):
      v = bound_levels[i]
      if 0 == i:
        continue

      delta_levels.append(v - bound_levels[i-1])

    return delta_levels

  def readCdf(self,iFile):
    """Return a cdf handle created by the available cdf library. python-netcdf4 and scipy suported (default:scipy)"""
    if not self.returnCdf:
      self.loadCdf()

    if ( "scipy" == self.cdfMod):
      #making it compatible to older scipy versions
      fileObj =  self.cdf.netcdf_file(iFile, mode='r')
    elif ( "netcdf4" == self.cdfMod ):
      fileObj = self.cdf.Dataset(iFile)
    else:
      raise ImportError,"Could not import data from file '" + iFile + "'"

    retval = fileObj
    return retval

  def openCdf(self,iFile):
    """Return a cdf handle created by the available cdf library. python-netcdf4 and scipy suported (default:scipy)"""
    if not self.returnCdf:
      self.loadCdf()

    if ( "scipy" == self.cdfMod):
      #making it compatible to older scipy versions
      print("Use scipy")
      fileObj =  self.cdf.netcdf_file(iFile, mode='r+')
    elif ( "netcdf4" == self.cdfMod ):
      print("Use netcdf4")
      fileObj = self.cdf.Dataset(iFile,'r+')
    else:
      raise ImportError,"Could not import data from file '" + iFile + "'"

    retval = fileObj
    return retval

  def readArray(self, iFile, varname):
    """Direcly return a numpy array for a given variable name"""
    filehandle = self.readCdf(iFile)
    if varname in filehandle.variables:
      # return the data array
      return filehandle.variables[varname][:]
    else:
      print "Cannot find variable '" + varname +"'"
      return False

  def readMaArray(self, iFile, varname):
    """Create a masked array based on cdf's FillValue"""
    fileObj =  self.readCdf(iFile)

    #.data is not backwards compatible to old scipy versions, [:] is
    data = fileObj.variables[varname][:]

    # load numpy if available
    try:
      import numpy as np
    except:
      raise ImportError,"numpy is required to return masked arrays."

    if hasattr(fileObj.variables[varname],'_FillValue'):
      #return masked array
      retval = np.ma.array(data,mask=data == fileObj.variables[varname]._FillValue)
    else:
      #generate dummy mask which is always valid
      retval = np.ma.array(data,mask=data != data )

    return retval

# Helper module for easy temp file handling
class MyTempfile(object):

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
      t = tempfile.NamedTemporaryFile(delete=True, prefix='ncoPy')
      self.__class__.__tempfiles.append(t.name)
      t.close()

      return t.name
    else:
      N =10000000
      t = "_"+random.randint(N).__str__()
