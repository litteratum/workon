"""setup.py for the script."""
from setuptools import setup, find_packages

setup(
    name='workon',
    version='0.0.4',
    author='Andrey Nechaev',
    author_email='andrewnech@gmail.com',
    packages=find_packages(exclude=('tests.*', 'tests')),
    entry_points={
        'console_scripts': ['workon = workon.main:main']
    },
)
