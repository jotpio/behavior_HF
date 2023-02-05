#!/usr/bin/env python

from distutils.core import setup

setup(
    install_requires=["llvmlite==0.39.1; python_version >= '3.7'", 'numba==0.56.4', 'numpy==1.23.5', 'pyqt5==5.12.3', "pyqt5-sip==12.11.1; python_version >= '3.7'", 'pyyaml==6.0', 'scipy==1.10.0', 'setuptools==67.1.0'],
    name="behavior_simulation",
    version="1.0",
    description="Behavior Simulation in the Humboldt Dorum",
    author="Jonas Piotrowski",
    author_email="marc.jonas.piotrowski@gmail.com",
    url="https://github.com/jotpio/behavior_HF",
    # packages=["distutils", "distutils.command"],
)