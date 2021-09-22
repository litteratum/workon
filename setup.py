"""setup.py for the script."""
import os
import shutil
from setuptools import setup, find_packages
from setuptools.command.install import install


USER_CONFIG_PATH = os.path.expanduser('~/.config/git_workon/config.json')


class LocalInstall(install):

    def run(self):
        os.makedirs(os.path.dirname(USER_CONFIG_PATH), exist_ok=True)
        if not os.path.exists(USER_CONFIG_PATH):
            shutil.copy('config.json', USER_CONFIG_PATH)
        install.run(self)


setup(
    name='git_workon',
    version='1.1.0',
    author='Andrey Nechaev',
    author_email='andrewnech@gmail.com',
    packages=find_packages(exclude=('tests.*', 'tests')),
    entry_points={
        'console_scripts': ['git_workon = git_workon.main:main']
    },
    cmdclass={
        'install': LocalInstall,
    },
)
