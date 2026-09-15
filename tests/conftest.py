import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]


def load_module(module_name, relative_path, monkeypatch=None, env_name=None):
    if monkeypatch is not None and env_name:
        monkeypatch.setenv(env_name, "sqlite:///:memory:")

    module_path = ROOT / relative_path
    module_dir = str(module_path.parent)
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
