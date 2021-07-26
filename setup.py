"""setup.py for the script."""
import os
from setuptools import setup, find_packages

setup(
    name='workon',
    version='0.3.0',
    author='Andrey Nechaev',
    author_email='andrewnech@gmail.com',
    packages=find_packages(exclude=('tests.*', 'tests')),
    entry_points={
        'console_scripts': ['workon = workon.main:main']
    },
    data_files=[
        (os.path.expanduser('~/.config/workon/'), ['config.json']),
    ]
)
