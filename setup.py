# encoding: utf-8
from setuptools import setup

setup(
    name='pyvcd',
    author='Peter Grayson',
    author_email='pete@jpgrayson.net',
    description='Python VCD file support.',
    long_description='\n\n'.join(
        open(f, 'rb').read().decode('utf-8')
        for f in ['README.rst', 'LICENSE.txt']),
    url='http://pyvcd.readthedocs.io/en/latest/',
    download_url='https://github.com/SanDisk-Open-Source/pyvcd',
    license='MIT',
    setup_requires=['setuptools_scm'],
    use_scm_version=True,
    install_requires=['six'],
    packages=['vcd'],
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Electronic Design Automation '
        '(EDA)',
    ],
)
