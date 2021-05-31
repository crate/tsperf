import setuptools

__version__ = "1.1.0"

with open("README.md", "r") as fh:
    long_description = fh.read()

requires = [
    "blessed==1.18.0",
    "boto3==1.17.84",
    "botocore~=1.20.84",
    "crate==0.26.0",
    "prometheus_client==0.10.1",
    "urllib3==1.26.5",
    "datetime_truncate==1.1.1",
    "psycopg2-binary==2.8.6",
    "influxdb_client==1.17.0",
    "pymongo==3.11.4",
    "numpy==1.20.3",
    "pgcopy==1.5.0",
    "pyodbc==4.0.30",
    "tqdm==4.61.0",
    "cloup==0.8.2",
]

test_requires = [
    "pytest==6.2.4",
    "pytest-cov==2.12.0",
    "dotmap==1.3.23",
    "flakehell==0.9.0",
    "flake8==3.9.2",
    "flake8-black==0.2.1",
    "flake8-bugbear==21.4.3",
    "flake8-bandit==2.1.2",
    "flake8-isort==4.0.0",
    "black==21.5b1",
    "isort==5.8.0",
]

setuptools.setup(
    name="tsperf",
    version=__version__,
    author="Crate.io",
    author_email="office@crate.at",
    description="A tool to test performance of different time-series databases",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/crate/tsperf",
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
            "tsperf = tsperf.cli:main",
        ]
    },
    install_requires=requires,
    extras_require={"testing": test_requires},
    python_requires='>=3.7',
    include_package_data=True,
    package_data={
        "": ["*.md", "*.json"],
    },
    zip_safe=False,
)
