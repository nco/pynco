"""
setup.py
"""

from setuptools import setup

version = "1.0.0"

setup(
    name="nco",
    version=version,
    author="Joe Hamman",
    author_email="jhamman@ucar.edu",
    license="MIT",
    description="""python bindings to NCO""",
    packages=["nco"],
    py_modules=["nco.nco", "nco.custom"],
    url="https://github.com/nco/pynco",
    download_url="https://raw2.github.com/nco/pynco/tarball/{0}".format(version),
    keywords=["netcdf", "climate"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Utilities",
        "Operating System :: POSIX",
        "Programming Language :: Python",
    ],
    python_requires='>=3.6',
    tests_require=["dateutil", "h5py", "netcdf4", "numpy", "pytest", "scipy"],
)
