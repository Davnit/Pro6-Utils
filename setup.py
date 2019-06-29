#!/usr/bin/env python3

from setuptools import setup, find_packages


setup(
    name="pro6-utils",
    version="1.1",
    description="Interface for manipulating ProPresenter 6 environments.",
    author="Davnit",
    author_email="david@davnit.net",
    packages=find_packages(),
    install_requires=["hachoir>=3.0a3"]
)
