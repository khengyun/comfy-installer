import random
import shutil
import subprocess
import sys
import os
import platform
import time
import urllib
from urllib.parse import urlparse
import zipfile

import git
from git import RemoteProgress
from tqdm import tqdm
from .common import find_git_root

def get_node_installer():
    """
    Returns an instance of NodeInstaller with a file downloader for handling node installation.

    Example:
        file_downloader = FileDownloader().download_file
        installer = get_node_installer()

    Returns:
        NodeInstaller: An instance of the NodeInstaller class.
    """
    from .file_downloader import FileDownloader

    file_downloader = FileDownloader().download_file
    return NodeInstaller(file_downloader)

class NodeInstaller:
    """
    A class for installing custom nodes from various sources (git, zip, or copy).

    Attributes:
        comfy_path (str): Path to the ComfyUI directory.
        comfyui_manager_path (str): Path to the ComfyUI Manager directory.
        custom_nodes_path (str): Path to the custom nodes directory.
        js_path (str): Path to the JavaScript extensions directory.
        git_script_path (str): Path to the git helper script.
        startup_script_path (str): Path to the startup scripts.
        download_url (function): Function to download files.
    """

    def __init__(self, file_downloader):
        """
        Initializes the NodeInstaller class.

        This version uses the current working directory to locate the ComfyUI folder.

        Args:
            file_downloader (function): A function to download files.
        """
        # Set the ComfyUI folder based on the current working directory.
        self.comfy_path = os.path.join(os.getcwd(), "ComfyUI")
        print("ComfyUI folder path:", self.comfy_path)
        
        self.comfyui_manager_path = os.path.abspath(
            os.path.join(self.comfy_path, "custom_nodes", "ComfyUI-Manager")
        )
        print("ComfyUI Manager path:", self.comfyui_manager_path)
        
        # The custom nodes folder is directly under ComfyUI/custom_nodes.
        self.custom_nodes_path = os.path.abspath(
            os.path.join(self.comfy_path, "custom_nodes")
        )
        self.js_path = os.path.join(self.comfy_path, "web", "extensions")
        self.git_script_path = os.path.join(self.comfyui_manager_path, "git_helper.py")
        self.startup_script_path = os.path.join(self.comfyui_manager_path, "startup-scripts")
        self.download_url = file_downloader

    def clone_comfyui(self):
        """
        Clones the ComfyUI repository from https://github.com/comfyanonymous/ComfyUI.git
        into the local ComfyUI folder if it does not already exist.

        Returns:
            bool: True if ComfyUI exists (or is cloned successfully), False otherwise.

        Example:
            clone_comfyui() -> True
        """
        repo_url = "https://github.com/comfyanonymous/ComfyUI.git"
        if not os.path.exists(self.comfy_path):
            print("ComfyUI not found. Cloning from", repo_url)
            try:
                repo = git.Repo.clone_from(repo_url, self.comfy_path)
                print("Successfully cloned ComfyUI!")
            except Exception as e:
                print(f"Error cloning ComfyUI: {e}")
                return False
        else:
            print("ComfyUI folder already exists.")
        return True

    def _is_valid_url(self, url):
        """
        Checks if the URL is valid and appends `.git` if missing, or removes trailing slashes and appends `.git`.

        Args:
            url (str): The URL of the Git repository.

        Returns:
            bool: True if the URL is valid, False otherwise.

        Example:
            _is_valid_url('https://github.com/user/repo') -> True
            _is_valid_url('https://github.com/user/repo/') -> True
        """
        try:
            if not url.endswith(".git"):
                if url.endswith("/"):
                    url = url.rstrip("/") + ".git"
                else:
                    url = url + ".git"
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def _run_script(self, cmd, cwd="."):
        """
        Runs a script with the given command.

        Args:
            cmd (list): The command to run as a list of strings.
            cwd (str): The working directory where the command will be run (default is the current directory).

        Returns:
            int: The return code of the command.

        Example:
            _run_script(['python', 'script.py'], cwd='scripts/')
        """
        if len(cmd) > 0 and cmd[0].startswith("#"):
            print(f"[ComfyUI-Manager] Unexpected behavior: `{cmd}`")
            return 0
        subprocess.check_call(cmd, cwd=cwd)
        return 0

    def _gitclone(self, custom_nodes_path, url, target_hash=None):
        """
        Clones a Git repository and optionally checks out a specific commit or branch.

        Args:
            custom_nodes_path (str): The path to the custom nodes directory.
            url (str): The Git URL of the repository.
            target_hash (str, optional): The specific commit hash or branch to checkout (default is None).

        Returns:
            bool: True if the repository was successfully cloned, False otherwise.

        Example:
            _gitclone(custom_nodes_path='/path/to/nodes', url='https://github.com/user/repo.git') -> True
        """
        repo_name = os.path.splitext(os.path.basename(url))[0]
        repo_path = os.path.join(custom_nodes_path, repo_name)
        print("Cloning to:", repo_path)
        max_retries = 5
        for attempt in range(max_retries):
            try:
                if os.path.exists(repo_path):
                    shutil.rmtree(repo_path)
                repo = git.Repo.clone_from(url, repo_path, recursive=True, progress=GitProgress())
                print(f"Available branches in {repo_name}:")
                for branch in repo.branches:
                    print(branch.name)
                if target_hash is not None:
                    print(f"CHECKOUT: {repo_name} [{target_hash}]")
                    repo.git.checkout(target_hash)
                else:
                    print(f"CHECKOUT: {repo_name} [main]")
                    repo.git.checkout('main')
                repo.git.clear_cache()
                repo.close()
                print(f"Successfully cloned {repo_name}")
                return True
            except Exception as e:
                print(f"An unexpected error occurred while cloning {repo_name}: {str(e)}")
                if attempt < max_retries - 1:
                    delay = 0.5
                    print(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    print(f"Failed to clone {repo_name} after {max_retries} attempts")
        return False

    def _gitclone_install(self, files, commit_hash_list=None):
        """
        Installs nodes by cloning repositories from the provided Git URLs.

        Args:
            files (list): A list of Git repository URLs.
            commit_hash_list (list, optional): A list of commit hashes or branch names corresponding to each URL.
                                               Defaults to an empty list if not provided.

        Returns:
            bool: True if all repositories were successfully installed, False otherwise.

        Example:
            _gitclone_install(['https://github.com/user/repo'], ['main']) -> True
        """
        if commit_hash_list is None:
            commit_hash_list = []
        print(f"Install: {files}")
        overall_status = True
        for idx, url in enumerate(files):
            if not self._is_valid_url(url):
                print(f"Invalid git url: '{url}'")
                return False
            if url.endswith("/"):
                url = url[:-1]
            max_retries = 5
            status = True
            for attempt in range(max_retries):
                try:
                    print(f"Download: git clone '{url}'")
                    repo_name = os.path.splitext(os.path.basename(url))[0]
                    repo_path = os.path.join(self.custom_nodes_path, repo_name)
                    res = self._gitclone(
                        self.custom_nodes_path,
                        url,
                        commit_hash_list[idx] if idx < len(commit_hash_list) else None,
                    )
                    if not res:
                        status = False
                        break
                    if not self._execute_install_script(url, repo_path):
                        status = False
                    break
                except Exception as e:
                    print(f"Install(git-clone) error: {url} / {e}", file=sys.stderr)
                    print("***** RETRYING...")
                    time.sleep(0.5)
            if not status:
                overall_status = False
        print("Installation was " + ("successful" if overall_status else "unsuccessful"))
        return overall_status

    def _unzip_install(self, files):
        """
        Downloads and extracts files from URLs.

        Args:
            files (list): A list of URLs to download and extract.

        Returns:
            bool: True if the files were successfully downloaded and extracted, False otherwise.

        Example:
            _unzip_install(['https://example.com/file.zip']) -> True
        """
        temp_filename = "manager-temp.zip"
        for url in files:
            if url.endswith("/"):
                url = url[:-1]
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
                }
                req = urllib.request.Request(url, headers=headers)
                response = urllib.request.urlopen(req)
                data = response.read()
                with open(temp_filename, "wb") as f:
                    f.write(data)
                with zipfile.ZipFile(temp_filename, "r") as zip_ref:
                    zip_ref.extractall(self.custom_nodes_path)
                os.remove(temp_filename)
            except Exception as e:
                print(f"Install(unzip) error: {url} / {e}")
                return False
        print("Installation was successful.")
        return True

    def _copy_install(self, files, js_path_name=None):
        """
        Downloads and copies files to the specified directory.

        Args:
            files (list): A list of file URLs to download and copy.
            js_path_name (str, optional): The specific directory to copy files to (default is None).

        Returns:
            bool: True if the files were successfully copied, False otherwise.

        Example:
            _copy_install(['https://example.com/file.py'], js_path_name='extensions') -> True
        """
        for url in files:
            if url.endswith("/"):
                url = url[:-1]
            try:
                if url.endswith(".py"):
                    self.download_url(url, self.custom_nodes_path)
                else:
                    path = (
                        os.path.join(self.js_path, js_path_name)
                        if js_path_name is not None
                        else self.js_path
                    )
                    if not os.path.exists(path):
                        os.makedirs(path)
                    self.download_url(url, path)
            except Exception as e:
                print(f"Install(copy) error: {url} / {e}")
                return False
        print("Installation was successful.")
        return True

    def _execute_install_script(self, url, repo_path):
        """
        Executes the install script and installs dependencies using uv if a requirements.txt file is present.
        
        Since you are using uv instead of pip, this function calls 'uv add -r requirements.txt'
        to install the dependencies from the requirements file.

        Args:
            url (str): The Git URL of the repository (for logging purposes).
            repo_path (str): The local path to the cloned repository.

        Returns:
            bool: True if the installation script (and uv dependency installation) executed successfully, False otherwise.

        Example:
            _execute_install_script('https://github.com/user/repo.git', '/path/to/repo') -> True
        """
        install_script_path = os.path.join(repo_path, "install.py")
        requirements_path = os.path.join(repo_path, "requirements.txt")
        if os.path.exists(requirements_path):
            print("Installing dependencies using uv from requirements.txt")
            uv_install_cmd = ["uv", "add", "-r", requirements_path]
            try:
                self._run_script(uv_install_cmd, cwd=repo_path)
            except Exception as e:
                print(f"Error installing dependencies with uv for {url}: {e}")
                return False
        if os.path.exists(install_script_path):
            print("Install: Running install script")
            install_cmd = [sys.executable, "install.py"]
            try:
                self._run_script(install_cmd, cwd=repo_path)
            except Exception as e:
                print(f"Error running install script for {url}: {e}")
                return False
        return True

    def _remap_pip_package(self, pkg):
        """
        Remaps certain pip packages if needed.

        Args:
            pkg (str): The package name.

        Returns:
            str: The remapped package name if a mapping exists, otherwise the original package name.

        Example:
            _remap_pip_package('imageio[ffmpeg]') -> 'imageio'
        """
        pip_overrides = {}
        if pkg in pip_overrides:
            res = pip_overrides[pkg]
            print(f"[ComfyUI-Manager] '{pkg}' is remapped to '{res}'")
            return res
        else:
            return pkg

    def install_node(self, json_data):
        """
        Installs a node based on the provided installation data (unzip, copy, or git-clone).

        Args:
            json_data (dict): A dictionary containing the installation type and files.

        Returns:
            bool: True if the node was successfully installed, False otherwise.

        Example:
            install_node({
                "install_type": "git-clone",
                "files": ["https://github.com/user/repo.git"]
            }) -> True
        """
        install_type = json_data["install_type"]
        if install_type == "unzip":
            res = self._unzip_install(json_data["files"])
        elif install_type == "copy":
            js_path_name = json_data["js_path"] if "js_path" in json_data else "."
            res = self._copy_install(json_data["files"], js_path_name)
        elif install_type == "git-clone":
            res = self._gitclone_install(
                json_data["files"], json_data.get("commit_hash", [])
            )
        if "pip" in json_data:
            for pname in json_data["pip"]:
                pkg = self._remap_pip_package(pname)
                install_cmd = [sys.executable, "-m", "pip", "install", pkg]
                try:
                    self._run_script(install_cmd, cwd=".")
                except Exception as e:
                    print(f"error installing {json_data['files'][0]}")
        return True if res else False

class GitProgress(RemoteProgress):
    """
    A progress bar for Git clone operations.

    Attributes:
        pbar (tqdm): The progress bar for the operation.
    """
    def __init__(self):
        super().__init__()
        self.pbar = tqdm()

    def update(self, op_code, cur_count, max_count=None, message=""):
        """
        Updates the progress bar during the Git operation.

        Args:
            op_code (str): The operation code.
            cur_count (int): The current count of the operation.
            max_count (int, optional): The maximum count for the operation.
            message (str, optional): A message to display with the progress.

        Example:
            update(op_code='clone', cur_count=50, max_count=100)
        """
        self.pbar.total = max_count
        self.pbar.n = cur_count
        self.pbar.pos = 0
        self.pbar.refresh()
