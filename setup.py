import setuptools

__version__ = "1.2.1"

with open("README.md", "r") as fh:
    long_description = fh.read()

requires = [
    "blessed<1.21",
    "boto3<1.35",
    "crate==0.35.2",
    "prometheus-client<0.11",
    "urllib3<3",
    "datetime-truncate<2",
    "psycopg2-binary<2.10",
    "influxdb-client<2",
    "pymongo<5",
    "dnspython<3",
    "numpy<1.27",
    "pgcopy<1.7",
    "pyodbc<6",
    "tqdm<5",
    "cloup<4",
]

develop_requires = [
    "mypy<1.11",
    "poethepoet<0.27",
    "pyproject-fmt<1.8",
    "ruff<0.5",
    "sphinx-autobuild==2021.3.14",  # Newer versions stopped "watching" appropriately?
    "validate-pyproject<0.17",
]

docs_requires = [
    "furo",
    "myst-parser[linkify]<3,>=0.18",
    "sphinx<7",
    "sphinx-copybutton",
    "sphinx-design-elements<1",
    "sphinxcontrib-mermaid<1",
    "sphinxext-opengraph<1",
]

release_requires = [
    "build<2",
    "twine<6",
]

test_requires = [
    "dotmap<1.4",
    "pytest<9",
    "pytest-cov<6",
    "ruff<0.5",
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
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications",
        "Topic :: Database",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator",
        "Topic :: Software Development :: Libraries",
        "Topic :: Text Processing",
        "Topic :: Utilities",
        "Operating System :: POSIX",
        "Operating System :: Unix",
        "Operating System :: MacOS",
    ],
    entry_points={
        "console_scripts": [
            "tsperf = tsperf.cli:main",
        ]
    },
    install_requires=requires,
    extras_require={
        "develop": develop_requires,
        "docs": docs_requires,
        "release": release_requires,
        "test": test_requires,
    },
    python_requires=">=3.8",
    include_package_data=True,
    package_data={
        "": ["*.md", "*.json"],
    },
    zip_safe=False,
)
