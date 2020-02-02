# File: setup.py
# Date: 27-Apr-2019
#
# Updates:
#
#
import re

from setuptools import find_packages
from setuptools import setup
from setuptools.command.install import install as _install


class Install(_install):
    def run(self):
        # _install.do_egg_install(self)
        import nltk  # pylint: disable=import-outside-toplevel

        # nltk.download("all")
        nltk.download("popular")


packages = []
thisPackage = "rcsb.utils.citation"

with open("rcsb/utils/citation/__init__.py", "r") as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', fd.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError("Cannot find version information")

setup(
    name=thisPackage,
    version=version,
    description="RCSB Python utility classes to manage PDB citation data",
    long_description="See:  README.md",
    author="John Westbrook",
    author_email="john.westbrook@rcsb.org",
    url="https://github.com/rcsb/py-rcsb_utils_citation",
    #
    license="Apache 2.0",
    classifiers=(
        "Development Status :: 3 - Alpha",
        # 'Development Status :: 5 - Production/Stable',
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
    ),
    entry_points={"console_scripts": []},
    #
    # cmdclass={"install": Install},
    install_requires=["rcsb.utils.io >= 0.52", "rcsb.utils.config >= 0.30", "nltk >= 3.2.5", "regex >= 2019.11.1"],
    # setup_requires=["nltk"],
    packages=find_packages(exclude=["rcsb.mock-data", "rcsb.utils.tests-citation", "rcsb.utils.tests-*", "tests.*"]),
    package_data={
        # If any package contains *.md or *.rst ...  files, include them:
        "": ["*.md", "*.rst", "*.txt", "*.cfg"]
    },
    #
    test_suite="rcsb.utils.tests-citation",
    tests_require=["tox"],
    #
    # Not configured ...
    extras_require={"dev": ["check-manifest"], "test": ["coverage"]},
    # Added for
    command_options={"build_sphinx": {"project": ("setup.py", thisPackage), "version": ("setup.py", version), "release": ("setup.py", version)}},
    # This setting for namespace package support -
    zip_safe=False,
)
