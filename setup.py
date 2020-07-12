from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='xdcc_downloader',
    version='1.0',
    description='A simple script to download xdcc files from irc servers.',
    license="GNU",
    long_description=long_description,
    author='Mahir Ashab',
    author_email='mahirashab19@gmail.com',
    url="https://github.com/mahirashab/XDCC-Downloader",
    platforms=["Windows", "Linux"],
    scripts=['bin/xdcc-bot'],
    packages=find_packages(),
    install_requires=[
        'colorama>=0.4.3',
        'names>=0.3.0',
        'puffotter>=0.9.6',
        'PyInquirer>=1.0.3'
    ],
    classifiers=[
        'Environment :: Console',
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3.6',
        'Topic :: Text Processing :: Linguistic',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
      ],
    include_package_data=True,
    zip_safe=False
)