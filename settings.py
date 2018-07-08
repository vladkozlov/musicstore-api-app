import pathlib
import yaml

BASE_DIR = pathlib.Path(__file__).parent
DB_CFG = BASE_DIR / 'config' / 'postgres_cfg.yaml'
APP_CFG = BASE_DIR / 'config' / 'app.yaml'


def get_config(path=DB_CFG):
    with open(path) as f:
        config = yaml.load(f)
    return config