"""Package configuration for upstox_instrument_query.

This module contains the package configuration for setuptools
to build and distribute the upstox_instrument_query package.
"""

from setuptools import find_packages, setup

setup(
    name="upstox_instrument_query",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests==2.32.3",
    ],
    extras_require={
        "dev": [
            "pytest==8.3.5",
            "pytest-cov==6.1.1",
            "pre-commit==4.2.0",
            "coverage==7.8.0",
        ],
        "test": [
            "pytest==8.3.5",
            "pytest-cov==6.1.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "upstox-query=upstox_instrument_query.cli:main",
        ],
    },
    author="Jinto A G",
    author_email="project.jintoag@gmail.com",
    description=(
        "Efficiently query large Upstox instruments " "JSON files using SQLite"
    ),
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/jinto-ag/upstox_instrument_query",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Financial :: Investment",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Developers",
    ],
    python_requires=">=3.9",
)
