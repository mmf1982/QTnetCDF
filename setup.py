from setuptools import setup, find_packages
# python3.7 -m pip uninstall QTnetCDF
# python3.7 -m setup install --user  # inside corresponding direcory
with open("requirements_dev.txt", "r") as fid:
    requirements = fid.read().split("\n")

setup(
    name="QTnetCDF",
    version="0.0.4",
    author="Martina M Friedrich",
    author_email="5464@gmx.net",
    description="A package to interactively view netCDF and hdf4/ hdf5 files using QT",
    #long_description=readme,
    #long_description_content_type="text/markdown",
    url="https://github.com/mmf1982/QTnetCDF/",
    packages=find_packages(),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
)
