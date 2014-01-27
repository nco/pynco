#!/bin/bash

# Install Dependencies
# as of pip 1.4rc2, wheel files are still being broken regularly, this is a
# known good commit. should revert to pypi when a final release is out
pip_commit=42102e9deaea99db08b681d06906c2945f6f95e2
pip install -I git+https://github.com/pypa/pip@$pip_commit#egg=pip

python_major_version="${TRAVIS_PYTHON_VERSION:0:1}"
[ "$python_major_version" == "2" ] && python_major_version=""

pip install -I -U setuptools
pip install wheel

# comment this line to disable the fetching of wheel files
base_url=http://cache27diy-cpycloud.rhcloud.com
wheel_box=${TRAVIS_PYTHON_VERSION}${JOB_TAG}
PIP_ARGS+=" -I --use-wheel --find-links=$base_url/$wheel_box/"

time pip install $PIP_ARGS -r ci/requirements-${wheel_box}.txt

# install netcdf packages
time sudo apt-get $APT_ARGS install nco python-netcdf

# we need these for numpy
time sudo apt-get $APT_ARGS install libatlas-base-dev gfortran

# build and install nco.py
time sudo python NCOpy/setup.py install

true
