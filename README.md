# Comfy Installer

**Comfy Installer** is a CLI tool that simplifies installing custom nodes and models for [ComfyUI](https://github.com/comfyanonymous/ComfyUI). It uses a YAML configuration to automate the setup, ensuring that all dependencies, custom nodes, and model files are installed correctly.

## Features

- **Easy Custom Node Installation**  
  Install nodes from GitHub repositories, ZIP files, or direct file copy.

- **Automatic Model Download**  
  Fetches model files from URLs and places them into the correct ComfyUI directories.

- **YAML-Based Configuration**  
  Manage installations via a single YAML file, ensuring reproducible setups.

- **Workflow Integration**  
  The included `ComfyRunner` class can start ComfyUI, manage installations, and run workflows.

- **Lightweight & Extensible**  
  The tool is built with modular utilities, making it easy to customize or extend.

## Requirements

- **Python 3.9+**
- **pip** or a similar package manager

## Installation

### From PyPI with uv

```bash
uv add comfy-installer
```

### From Source

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/comfy-installer.git
   cd comfy-installer
   ```
2. Install dependencies:
   ```bash
   uv run pip install -r requirements.txt
   ```
3. (Optional) Install as a package:
   ```bash
   python setup.py install
   ```

## Usage

### 1. Prepare a YAML File

Create a YAML file (e.g., `config.yaml`) with the nodes and models you want to install:

```yaml
nodes:
  - name: "ComfyUI-AnimateDiff-Evolved"
    url: "https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved"
    install_type: "git-clone"

  - name: "ComfyUI-Advanced-ControlNet"
    url: "https://github.com/Kosinkadink/ComfyUI-Advanced-ControlNet"
    install_type: "git-clone"

models:
  - name: "sd_xl_base_18897557.0.safetensors"
    url: "https://civitai.com/api/download/models/299716"
    dest: "./ComfyUI/models/checkpoints/"

  - name: "mod_sdxl.safetensors"
    url: "https://civitai.com/api/download/models/299716"
    dest: "./ComfyUI/models/checkpoints/"

```

### 2. Run the Installer via CLI

```bash
comfy-install --yaml path/to/config.yaml [--install-dir /your/install/path]
```

## Contributing

1. Fork the repository.
2. Create a new branch: `git checkout -b feature/your-feature`.
3. Commit your changes: `git commit -m 'Add feature'`.
4. Push to the branch: `git push origin feature/your-feature`.
5. Open a pull request.

## License

This project is licensed under the [MIT License](LICENSE).

## Support

For issues or feature requests, please [open an issue](https://github.com/yourusername/comfy-installer/issues).

