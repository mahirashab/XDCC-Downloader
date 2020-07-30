from xdcc_bot._version import __version__
from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='xdcc-bot',
    version=__version__,
    description='A simple script to download xdcc files from irc servers.',
    license="GNU",
    long_description=long_description,
    author='Mahir Ashab',
    author_email='mahirashab19@gmail.com',
    url="https://github.com/mahirashab/XDCC-Downloader",
    packages=find_packages(),
    entry_points={
          'console_scripts': ['xdcc-bot=xdcc_bot.cli:main'],
      },
    install_requires=[
        'colorama',
        'names',
        'puffotter',
        'PyInquirer'
    ],
    classifiers=[
        'Topic :: Internet',
        'Environment :: Console',
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3.6(Above)',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
      ],
    include_package_data=True,
    zip_safe=False
)