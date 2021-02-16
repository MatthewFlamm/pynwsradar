import os

from setuptools import setup

exec(open("pynwsradar/version.py").read())

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="pynwsradar",
    version=__version__,
    license="MIT License",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MatthewFlamm/pynwsradar",
    author="Matthew Flamm",
    author_email="matthewflamm0@gmail.com",
    description="Python library to retrieve radar from NWS/NOAA",
    packages=["pynwsradar"],
    include_package_data=True,
    install_requires=[
        "requests",
        "Pillow",
        "numpy",
    ],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    entry_points={
        "console_scripts": ["pynwsradar=pynwsradar.console_script:main"],
    },
)
