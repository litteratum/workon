"""setup.py for the script."""
import os
import shutil
from setuptools import setup, find_packages
from setuptools.command.install import install


USER_CONFIG_PATH = os.path.expanduser('~/.config/git_workon/config.json')


with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()


class LocalInstall(install):

    def run(self):
        os.makedirs(os.path.dirname(USER_CONFIG_PATH), exist_ok=True)
        if not os.path.exists(USER_CONFIG_PATH):
            shutil.copy('config.json', USER_CONFIG_PATH)
        install.run(self)


setup(
    name='git_workon',
    version='1.2.3',
    author='Andrey Nechaev',
    author_email='andrewnech@gmail.com',
    description='Utility that automates projects clone/remove and checks for nonpushed changes on removal',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license_files = ('LICENSE',),
    url='https://github.com/ReturnedVoid/workon',
    packages=find_packages(exclude=('tests.*', 'tests')),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Topic :: Utilities',
    ],
    entry_points={
        'console_scripts': ['gw = git_workon.main:main']
    },
    data_files=[
        ('', ['config.json',]),
    ],
    cmdclass={
        'install': LocalInstall,
    },
)
