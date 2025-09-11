"""
Setup script for the MongoDB ETL package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mongodb-etl",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A high-performance Python ETL framework for MongoDB data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/mongodb-etl",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
    install_requires=[
        "pymongo>=3.12.0",
        "pandas>=1.3.0",
        "numpy>=1.20.0",
        "pyarrow>=6.0.0",
        "python-dotenv>=0.19.0",
        "jsonschema>=4.0.0",
        "psutil>=5.8.0",
    ],
    entry_points={
        "console_scripts": [
            "mongodb-etl=main:main",
        ],
    },
)
