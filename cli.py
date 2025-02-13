#!/usr/bin/env python
"""
CLI tool to install custom nodes and models using a YAML configuration file.

Usage:
    comfy-runner --yaml path/to/config.yaml [--install-dir /path/to/install]

If --install-dir is not provided, the current working directory (".") is used.
"""

import argparse
import os
from ComfyInstallers import YamlInstallers  # adjust the import path as needed

def main():
    parser = argparse.ArgumentParser(
        description="Install custom nodes and models using a YAML configuration file."
    )
    parser.add_argument(
        "--yaml",
        required=True,
        help="Path to the YAML configuration file."
    )
    parser.add_argument(
        "--install-dir",
        default=".",
        help="Installation directory (default is current directory '.')."
    )
    args = parser.parse_args()

    # Change the working directory to the specified installation directory.
    try:
        os.chdir(args.install_dir)
    except Exception as e:
        print(f"Error changing directory to '{args.install_dir}': {e}")
        return

    print("Installation directory set to:", os.getcwd())

    # Create an instance of YamlInstallers and run the download and install process.
    installer = YamlInstallers(args.yaml)
    installer.download_and_install()

if __name__ == "__main__":
    main()
