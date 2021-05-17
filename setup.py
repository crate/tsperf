import setuptools

__version__ = "1.1.0"

with open("README.md", "r") as fh:
    long_description = fh.read()

requires = [
    "blessed==1.17.12",
    "boto3==1.16.25",
    "botocore~=1.19.51",
    "crate==0.26.0",
    "prometheus_client==0.9.0",
    "urllib3==1.26.2",
    "datetime_truncate==1.1.1",
    "psycopg2-binary==2.8.6",
    "influxdb_client==1.12.0",
    "pymongo==3.11.2",
    "numpy==1.19.4",
    "pgcopy==1.4.3",
    "pyodbc==4.0.30",
]

test_requires = [
    "dotmap==1.3.23",
    "mock==4.0.2",
    "numpy==1.19.4",
    "pytest==6.1.2",
    "pytest-cov==2.10.1",
    "flake8==3.8.4",
    "black==21.5b1",
    "flakehell==0.9.0",
]

setuptools.setup(
    name="tsdg",
    version=__version__,
    author="Crate.io",
    author_email="office@crate.at",
    description="A tool to test performance of different timeseries databases",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/crate/tsdg",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Communications",
        "Topic :: Database",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator",
        "Topic :: Software Development :: Libraries",
        "Topic :: Text Processing",
        "Topic :: Utilities",
        "Operating System :: POSIX",
        "Operating System :: Unix",
        "Operating System :: MacOS"
    ],
    entry_points={
        "console_scripts": [
            "tsdg = data_generator.__main__:main",
            "tsqt = query_timer.__main__:main",
        ]
    },
    install_requires=requires,
    extras_require={"testing": test_requires},
    python_requires='>=3.6',
)
