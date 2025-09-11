"""
Setup script for the MongoDB ETL package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mongodb-etl",
    version="0.1.0",
    author="Dali Moussa",
    author_email="dali@example.com",
    description="High-performance Python ETL framework for transforming MongoDB data into ML datasets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dalimoussa/mongodb-etl",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Database",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pymongo>=3.12.0",
        "pandas>=1.3.0",
        "numpy>=1.20.0",
        "pyarrow>=6.0.0",
        "python-dotenv>=0.19.0",
        "jsonschema>=4.0.0",
        "psutil>=5.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.2.5",
            "pytest-cov>=2.12.0",
            "black>=21.5b2",
            "flake8>=3.9.2",
            "mypy>=0.812",
        ],
    },
    entry_points={
        "console_scripts": [
            "mongodb-etl=mongodb_etl.main:main",
        ],
    },
)
