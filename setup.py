"""Setup script for Invasive Species Tracker."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="invasive-species-tracker",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="AI-powered invasive species detection using satellite imagery",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/invasive-species-tracker",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: GIS",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "invasive-tracker=src.cli:main",
        ],
    },
)