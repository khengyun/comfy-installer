import yaml
import os
from tabulate import tabulate
from comfy_installer.utils.comfy.api import ComfyAPI
from comfy_installer.utils.file_downloader import FileDownloader, ModelDownloader
from comfy_installer.utils.node_installer import get_node_installer
from comfy_installer.utils.logger import LoggingType, app_logger

class YamlInstallers:
    def __init__(self, yaml_file_path):
        """
        Initializes the YamlInstallers instance.

        Args:
            yaml_file_path (str): Path to the YAML configuration file.
        """
        self.yaml_file_path = yaml_file_path
        self.model_downloader = ModelDownloader()
        self.node_installer = get_node_installer()
        
        # hardcode
        self.model_dir = os.path.join(self.node_installer.comfy_path, "models")

    def load_yaml(self):
        """
        Loads and parses the YAML configuration file.

        Returns:
            dict: Parsed YAML data.
        """
        with open(self.yaml_file_path, 'r') as file:
            return yaml.safe_load(file)

    def download_and_install(self):
        """
        First clones ComfyUI (if not already present), then installs custom nodes and downloads models
        as specified in the YAML configuration. Finally, shows a summary of the operations.
        """
        # Clone ComfyUI before installing custom nodes.
        if not self.node_installer.clone_comfyui():
            app_logger.log(LoggingType.ERROR, "Failed to clone ComfyUI. Aborting installation.")
            return

        data = self.load_yaml()
        node_results = []
        model_results = []

        if 'nodes' in data:
            node_results = self._install_nodes(data['nodes'])
        
        if 'models' in data:
            model_results = self._download_models(data['models'], self.model_dir)
            
        self._show_summary(node_results, model_results)

    def _install_nodes(self, nodes):
        """
        Installs custom nodes from the YAML configuration.

        Args:
            nodes (list): List of node configurations.

        Returns:
            list: A list of tuples (node_name, status) for each node.
        """
        results = []
        print("Installing nodes...")
        for node in nodes:
            node_name = node.get("name", "Unnamed Node")
            app_logger.log(LoggingType.INFO, f"Installing custom node {node_name}")
            install_data = {
                "files": [node["url"]],
                "install_type": node.get("install_type", "git-clone"),
                "commit_hash": node.get("commit_hash", None)
            }
            success = self.node_installer.install_node(install_data)
            status = "Success" if success else "Failure"
            results.append((node_name, status))
            if not success:
                app_logger.log(LoggingType.ERROR, f"Failed to install node {node_name}")
            else:
                app_logger.log(LoggingType.INFO, f"Successfully installed node {node_name}")
        return results

    def _download_models(self, models, model_dir):
        """
        Downloads models specified in the YAML configuration.
        Returns a list of tuples (model_name, status, details) for each model.
        """
        results = []
        print("Downloading models...")
        for model in models:
            model_name = model.get("name", "Unnamed Model")
            url = model.get("url")
            type = type if type is not None else "checkpoints"
            dest = os.path.join(model_dir, type)
            app_logger.log(LoggingType.INFO, f"Downloading model {model_name}")

            filename, yaml_url, yaml_dest = self.model_downloader.get_model_details(model_name)
            if filename is None or yaml_url is None or yaml_dest is None:
                filename = model_name
                url = model.get("url")
                dest = os.path.join(model_dir, type)
                status_bool, file_status = self.model_downloader.download_file(filename, url, dest)
                similar_models = []
            else:
                status_bool, similar_models, file_status = self.model_downloader.download_model(model_name)

            status = "Success" if status_bool else "Failure"
            detail = file_status
            if not status_bool and similar_models:
                detail += f" (alternatives: {', '.join(similar_models)})"
            results.append((model_name, status, detail))
            if not status_bool:
                app_logger.log(LoggingType.ERROR, f"Failed to download model {model_name}")
            else:
                app_logger.log(LoggingType.INFO, f"Successfully downloaded model {model_name}")
        return results

    def _show_summary(self, node_results, model_results):
        """
        Prints summary tables for installed nodes and downloaded models.

        Args:
            node_results (list): List of tuples (node_name, status) for nodes.
            model_results (list): List of tuples (model_name, status, details) for models.
        """
        total_nodes = len(node_results)
        total_models = len(model_results)

        print("\n=== Summary ===")
        print(f"Total Nodes: {total_nodes}")
        if node_results:
            print(tabulate(node_results, headers=["Node", "Status"], tablefmt="grid"))
        else:
            print("No nodes to install.")

        print(f"\nTotal Models: {total_models}")
        if model_results:
            print(tabulate(model_results, headers=["Model", "Status", "Details"], tablefmt="grid"))
        else:
            print("No models to download.")

# Example usage if running directly:
if __name__ == "__main__":
    yaml_path = "config.yaml"  # Update with your YAML file path.
    installer = YamlInstallers(yaml_path)
    installer.download_and_install()
