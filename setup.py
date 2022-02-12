"""setup.py for the script."""
from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


setup(
    name="git_workon",
    version="1.2.5",
    author="Andrey Nechaev",
    author_email="andrewnech@gmail.com",
    description=(
        "Utility that automates projects clone/remove and checks for nonpushed"
        " changes on removal"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    license_files=("LICENSE",),
    url="https://github.com/ReturnedVoid/workon",
    packages=find_packages(exclude=("tests.*", "tests")),
    install_requires=[
        "appdirs",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Topic :: Utilities",
    ],
    entry_points={"console_scripts": ["gw = git_workon.main:main"]},
    data_files=[
        ("", ["config.json"]),
    ],
)
