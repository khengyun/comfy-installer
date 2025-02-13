import os
from setuptools import setup, find_packages

# Read dependencies from requirements.txt
with open("requirements.txt", "r") as f:
    requirements = f.read().splitlines()

setup(
    name="comfy-install",
    version="0.1.0",
    description="A CLI tool to install custom nodes for ComfyUI using YAML configuration.",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "comfy-install=cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
