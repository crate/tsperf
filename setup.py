import setuptools

__version__ = "2.0.0"

with open("README.md", "r") as fh:
    long_description = fh.read()

requires = [
    "boto3==1.16.25",
    "botocore~=1.19.25",
    "crate==0.26.0",
    "prometheus_client==0.9.0",
    "urllib3==1.26.2",
    "datetime_truncate==1.1.1",
    "psycopg2==2.8.6",
    "influxdb_client==1.12.0",
    "pymongo==3.11.2",
    "numpy==1.19.4",
    "pgcopy==1.4.3",
    "tictrack==1.0.0",
    "float_simulator==1.0.1",
    "batch_size_automator==1.0.0",
    "pyodbc==4.0.30"
]

test_requires = [
    "numpy==1.19.4",
    "mock==4.0.2",
    "pytest==6.1.2",
    "pytest-cov==2.10.1",
    "flake8==3.8.4"
]

setuptools.setup(
    name="tsdb_data_generator",
    version=__version__,
    author="Crate.io",
    author_email="office@crate.at",
    description="A tool to test performance of different timeseries databases",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/crate/ts-data-generator",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
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
