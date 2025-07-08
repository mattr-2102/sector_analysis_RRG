import os
import yaml

# dynamic resolve the project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def get_paths():
    yaml_path = os.path.join(PROJECT_ROOT, 'config', 'paths.yaml')
    with open(yaml_path, 'r') as f:
        rel_paths = yaml.safe_load(f)

    # Convert relative paths to absolute based on local machine
    abs_paths = {key: os.path.join(PROJECT_ROOT, path) for key, path in rel_paths.items()}
    return abs_paths