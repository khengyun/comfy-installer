import os
from setuptools import setup, find_packages

def load_requirements():
    req_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(req_path):
        with open(req_path, "r") as f:
            return f.read().splitlines()
    return []

setup(
    name="comfy-installer",
    version="0.1.6",
    description="A CLI tool to install custom nodes for ComfyUI using YAML configuration.",
    author="khengyun",
    author_email="khaangnguyeen@gmail.com",
    packages=find_packages(),
    install_requires=load_requirements(),
    entry_points={
        "console_scripts": [
            "comfy-installer=cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
