import setuptools

__version__ = "1.1.0"

with open("README.md", "r") as fh:
    long_description = fh.read()

requires = [
    "blessed<1.21",
    "boto3<1.35",
    "crate==0.26.0",
    "prometheus-client<0.11",
    "urllib3<2",
    "datetime-truncate<2",
    "psycopg2-binary<2.10",
    "influxdb-client<2",
    "pymongo<5",
    "dnspython<3",
    "numpy<1.27",
    "pgcopy<1.7",
    #"pyodbc<5",
    "tqdm<5",
    "cloup<1",
]

test_requires = [
    "pytest<7",
    "pytest-cov<6",
    "dotmap<1.4",
    "flakehell==0.9.0",
    "flake8==3.8.4",
    # FIXME: Does not work per 2024-05-18
    # "flake8-bandit==2.1.2",
    "flake8-black<0.4",
    "flake8-bugbear<22",
    "flake8-isort<5",
    "black==21.5b1",
    "isort<5.9",
]

setuptools.setup(
    name="tsperf",
    version=__version__,
    author="Crate.io",
    author_email="office@crate.at",
    description="A tool to test performance of time-series databases",
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
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
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
