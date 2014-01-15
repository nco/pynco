
import unittest, os, tempfile, sys, glob
from stat import *
from nco import *
import numpy as np
import pylab as pl

# add local dir to search path

def plot(ary, ofile=False, title=None):
    pl.grid(True)

    if not None == title:
      pl.title(title)

    if 1 == ary.ndim:
      pl.plot(ary)
    else:
      pl.imshow(ary, origin='lower', interpolation='nearest')

    if not ofile:
      pl.show()
    else:
      pl.savefig(ofile, bbox_inches='tight', dpi=200)

def rm(files):
  for f in files:
    if os.path.exists(f):
      os.system("rm "+f)

class NcoTest(unittest.TestCase):

    def testNCO(self):
        nco = Nco()
        newNCO="/usr/bin/nco"
        if os.path.isfile(newNCO):
            nco.setNco(newNCO)
            self.assertEqual(newNCO,nco.getNco())
            nco.setNco('nco')

    def testDbg(self):
        nco = Nco()
        self.assertEqual(False, nco.debug)
        nco = Nco(debug=True)
        self.assertEqual(True, nco.debug)
        nco.debug = False

    def testOps(self):
        nco = Nco()
        ops = ['ncap2', 'ncatted', 'ncbo', 'nces', 'ncecat', 'ncflint', 'ncks','ncpdq', 'ncra', 'ncrcat', 'ncrename', 'ncwa', 'ncdump']
        for op in ops:
            self.assertTrue(op in nco.operators)

    def test_mod_version(self):
        nco = Nco()
        self.assertEqual('4.4.0', nco.module_version())

    def test_getOperators(self):
        nco = Nco()
        for op in ['ncap2', 'ncatted', 'ncbo', 'nces', 'ncecat', 'ncflint', 'ncks','ncpdq', 'ncra', 'ncrcat', 'ncrename', 'ncwa', 'ncdump']:
            self.assertTrue(op in dir(nco))

    def test_listAllOperators(self):
        nco = Nco()
        operators = nco.operators
        operators.sort()
        #print "\n".join(operators)

    def test_use_list_inputs(self):
        nco = Nco(debug=True)
        outfiles = ['foo.nc', 'bar.nc']
        nco.ncrcat(input=outfiles, output='out.nc')

    def test_ncra_mult_files(self):
        nco = Nco(debug=True)

    def test_ncra_single_file(self):
        nco = Nco(debug=True)

    def test_ncks_extract(self):
        nco = Nco(debug=True)

    def test_ncea_mult_files(self):
        nco = Nco(debug=True)

    def test_errorException(self):
        nco = Nco()
        self.assertFalse(hasattr(nco, 'nonExistingMethod'))
        self.failUnlessRaises(NCOException, nco.max)
        try:
            nco.max()
        except NCOException as e:
            self.assertTrue(e.returncode != 0)
            self.assertTrue(len(e.stderr) > 1)
            self.assertTrue(hasattr(e, 'stdout'))

        try:
            nco.stdatm(0,10,input="",output="")
        except NCOException as a:
            self.assertTrue(e.returncode != 0)
            self.assertTrue(len(e.stderr) > 1)
            self.assertTrue(hasattr(e, 'stdout'))

    def test_forceOutput(self):
        nco =Nco()
        nco.debug = True
        outs = []
        # tempfiles
        outs.append(nco.stdatm("0,10,20"))
        outs.append(nco.stdatm("0,10,20"))
        self.assertNotEqual(outs[0],outs[1])
        outs = []

        # deticated output, force = true (=defaut setting)
        ofile = 'test_force'
        outs.append(nco.stdatm("0,10,20",output = ofile))
        mtime0 = os.stat(ofile).st_mtime
        #to make it compatible with systems providing no nanos.
        import time
        time.sleep(1)
        outs.append(nco.stdatm("0,10,20",output = ofile))
        mtime1 = os.stat(ofile).st_mtime
        self.assertNotEqual(mtime0,mtime1)
        self.assertEqual(outs[0],outs[1])
        os.remove(ofile)
        outs = []

        # dedicated output, force = false
        ofile = 'test_force_false'
        outs.append(nco.stdatm("0,10,20", output=ofile,force=False))
        mtime0 = os.stat(outs[0]).st_mtime
        outs.append(nco.stdatm("0,10,20", output=ofile,force=False))
        mtime1 = os.stat(outs[1]).st_mtime
        self.assertEqual(mtime0,mtime1)
        self.assertEqual(outs[0],outs[1])
        os.remove(ofile)
        outs = []

        # dedicated output, global force setting
        ofile = 'test_force_global'
        nco.forceOutput = False
        outs.append(nco.stdatm("0,10,20",output = ofile))
        mtime0 = os.stat(outs[0]).st_mtime
        outs.append(nco.stdatm("0,10,20",output = ofile))
        mtime1 = os.stat(outs[1]).st_mtime
        self.assertEqual(mtime0,mtime1)
        self.assertEqual(outs[0],outs[1])
        os.remove(ofile)
        outs = []

# Now run tests for examples in nco documentation
class NcoReturnCDFTest(unittest.TestCase):

    def test_returnArray(self):
        nco = Nco()
        temperature = nco.stdatm(0,options = '-f nc', returnCdf = True).variables['T'][:]
        self.assertEqual(False, nco.stdatm(0,options = '-f nc',returnArray = 'TT'))
        temperature = nco.stdatm(0,options = '-f nc',returnArray = 'T')
        self.assertEqual(288.0,temperature.flatten()[0])
        pressure = nco.stdatm("0,1000",options = '-f nc -b F64',returnArray = 'P')
        self.assertEqual("[ 1013.25         898.54345604]",pressure.flatten().__str__())

    def test_returnMaArray(self):
        nco = Nco()
        nco.debug = True
        topo = nco.topo(options='-f nc', returnMaArray='topo')
        self.assertEqual(-1890.0, round(topo.mean()))
        bathy = nco.setrtomiss(0, 10000,
            input = nco.topo(options='-f nc'), returnMaArray='topo')
        self.assertEqual(-3386.0, round(bathy.mean()))
        oro = nco.setrtomiss(-10000,0,
            input = nco.topo(options='-f nc'), returnMaArray='topo')
        self.assertEqual(1142.0, round(oro.mean()))
        bathy = nco.remapnn('r2x2', input=nco.topo(options='-f nc'), returnMaArray='topo')
        self.assertEqual(-4298.0, bathy[0, 0])
        self.assertEqual(-2669.0, bathy[0, 1])
        ta = nco.remapnn('r2x2', input=nco.topo(options='-f nc'))
        tb = nco.subc(-2669.0,input=ta)
        withMask = nco.div(input=ta+" "+tb, returnMaArray='topo')
        self.assertEqual('--', withMask[0, 1].__str__())
        self.assertEqual(False, withMask.mask[0, 0])
        self.assertEqual(False, withMask.mask[1, 0])
        self.assertEqual(False, withMask.mask[1, 1])
        self.assertEqual(True, withMask.mask[0, 1])

    def test_returnCdf(self):
        nco = Nco()
        ofile = tempfile.NamedTemporaryFile(delete=True, prefix='ncoPy').name
        press = nco.stdatm("0", output=ofile, options="-f nc")
        self.assertEqual(ofile, press)
        a = nco.readCdf(press)
        variables = nco.stdatm("0", options="-f nc", returnCdf=True).variables
        print(variables)
        press = nco.stdatm("0", options="-f nc", returnCdf=True).variables['P'][:]
        self.assertEqual(1013.25, press.min())
        press = nco.stdatm("0", output=ofile, options="-f nc")
        self.assertEqual(ofile, press)
        nco.setReturnArray()
        outfile = 'test.nc'
        press = nco.stdatm("0", output=outfile, options="-f nc").variables["P"][:]
        self.assertEqual(1013.25, press.min())
        nco.unsetReturnArray()
        press = nco.stdatm("0", output=outfile, options="-f nc")
        self.assertEqual(press, outfile)
        press = nco.stdatm("0", output=outfile, options="-f nc", returnCdf=True).variables["P"][:]
        self.assertEqual(1013.25, press.min())
        print("press = "+press.min().__str__())
        nco.unsetReturnArray()
        press = nco.stdatm("0", output=ofile, options="-f nc")
        self.assertEqual(ofile, press)


    def test_combine(self):
        nco = Nco()
        nco.debug = True
        stdatm  = nco.stdatm("0", options="-f nc")
        stdatm_ = nco.stdatm("0", options="-f nc")
        print(nco.diff(input=stdatm + " " + stdatm_))
        sum = nco.fldsum(input = stdatm)
        sum = nco.fldsum(input = nco.stdatm("0",options="-f nc"),returnCdf=True)
        self.assertEqual(288.0,sum.variables["T"][:])

    def test_cdf(self):
        nco = Nco()
        self.assertTrue("cdf" not in nco.__dict__)
        nco.setReturnArray()
        self.assertTrue("cdf" in nco.__dict__)
        nco.setReturnArray(False)
        sum = nco.fldsum(input = nco.stdatm("0",options="-f nc"),returnCdf=True)
        self.assertEqual(1013.25,sum.variables["P"][:])
        nco.unsetReturnArray()

    def test_cdf_mod_scipy(self):
        nco = Nco()
        nco.setReturnArray()
        print('nco.cdfMod:' + nco.cdfMod)
        self.assertEqual(nco.cdfMod, "scipy")

    def test_cdf_mod_netcdf4(self):
        nco =Nco(cdfMod='netcdf4')
        nco.setReturnArray()
        print('nco.cdfMod:' + nco.cdfMod)
        self.assertEqual(nco.cdfMod, "netcdf4")

    def test_inputArray(self):
        nco = Nco()
        nco.debug = 'DEBUG' in os.environ
        # check for file input
        fileA = nco.stdatm(0, output='A')
        fileB = nco.stdatm(0, output='B')
        files = [fileA,fileB]
        self.assertEqual(nco.diffv(input=' '.join(files)), nco.diffv(input=files))
        self.assertEqual([], nco.diffv(input=files))
        # check for operator input
        self.assertEqual([], nco.diffv(input = ["-stdatm, 0", "-stdatm, 0"]))
        # check for operator input and files
        self.assertEqual([], nco.diffv(input = ["-stdatm, 0",fileB]))

    def test_output_set_to_none(self):
        nco = Nco()
        self.assertEqual(str, type(nco.topo(output=None)))
        self.assertEqual("File format: GRIB", nco.sinfov(input="-topo", output=None)[0])

    def test_returnNone(self):
        nco = Nco()
        self.assertFalse(nco.returnNoneOnError,  "'returnNoneOnError' is _not_ False after initialization")
        nco.returnNoneOnError = True
        self.assertTrue(nco.returnNoneOnError, "'returnNoneOnError' is _not_ True after manual setting")
        ret  = nco.sinfo(input="-topf")
        self.assertEqual(None, ret)
        print(ret)

        nco_ = Nco(returnNoneOnError=True)
        self.assertTrue(nco_.returnNoneOnError)
        ret  = nco_.sinfo(input=" ifile.grb")
        self.assertEqual(None, ret)
        print(ret)

    def test_initOptions(self):
        nco = Nco(debug=True)
        self.assertTrue(nco.debug)
        nco = Nco(forceOutput=False)
        self.assertFalse(nco.forceOutput)
        nco = Nco(True,True)
        self.assertTrue(nco.returnCdf)
        nco.returnCdf = False
        self.assertTrue(not nco.returnCdf)
        self.assertTrue(nco.returnNoneOnError)

    def test_env(self):
        # clean up
        tag = '__env_test'
        files = glob.glob(tag+'*')
        rm(files)
        files = glob.glob(tag+'*')
        self.assertEqual([],files)

        # setup
        nco = Nco()
        nco.debug = 'DEBUG' in os.environ

        # cdf default
        ifile = nco.stdatm(10,20,50,100, options='-f nc')
        nco.splitname(input=ifile, output=tag)
        files = glob.glob(tag+'*')
        self.assertEqual(['__env_testP.nc', '__env_testT.nc'],files)
        rm(files)

        # manual setup to nc2 via operator call
        nco.splitname(input=ifile,output=tag,env={"NCO_FILE_SUFFIX": ".nc2"})
        files = glob.glob(tag+'*')
        files.sort()
        self.assertEqual(['__env_testP.nc2', '__env_testT.nc2'],files)
        rm(files)

        # manual setup to nc2 via object setup
        nco.env = {"NCO_FILE_SUFFIX": ".foo"}
        nco.splitname(input=ifile, output=tag)
        files = glob.glob(tag+'*')
        files.sort()
        self.assertEqual(['__env_testP.foo', '__env_testT.foo'],files)
        rm(files)

    def test_showMaArray(self):
        nco = Nco(cdfMod='netcdf4')
        nco.debug = True
        bathy = nco.setrtomiss(0,10000,
            input = nco.topo(options='-f nc'), returnMaArray='topo')
        pl.imshow(bathy,origin='lower')
        pl.show()
        oro = nco.setrtomiss(-10000,0,
            input = nco.topo(options='-f nc'), returnMaArray='topo')
        pl.imshow(oro,origin='lower')
        pl.show()
        random = nco.setname('test_maArray',
                             input = "-setrtomiss,0.4,0.8 -random,r180x90 ",
                             returnMaArray='test_maArray',
                             options = "-f nc")
        pl.imshow(random,origin='lower')
        pl.show()
        rand = nco.setname('v',input = '-random,r5x5 ', options = ' -f nc',output = '/tmp/rand.nc')


if __name__ == '__main__':
    unittest.main()

# vim:sw=2
