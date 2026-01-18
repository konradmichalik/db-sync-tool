import setuptools
import sys
from db_sync_tool import info

if sys.version_info < (3, 10):
    sys.exit('db_sync_tool requires Python 3.10+ to run')

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='db_sync_tool-kmi',
    version=info.__version__,
    author='Konrad Michalik',
    author_email='support@konradmichalik.eu',
    description='Synchronize a database from and to host systems.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url=info.__homepage__,
    license='MIT',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Topic :: Database',
        'Intended Audience :: Developers'
    ],
    python_requires='>=3.10',
    install_requires=[
        "paramiko>=4.0",
        "pyyaml>=6.0.2",
        "jsonschema>=4.20",
        "requests>=2.31.0",
        "semantic_version>=2.10.0",
        "rich>=13.0",
        "typer[all]>=0.15.0"
    ],
    entry_points={
        'console_scripts': [
            'db_sync_tool = db_sync_tool.__main__:main'
        ]
    },
)
