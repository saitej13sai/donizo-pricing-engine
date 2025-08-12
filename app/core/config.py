import os, yaml
CONFIG_PATH = os.getenv("CONFIG_PATH", "./config.yaml")
CONFIG = yaml.safe_load(open(CONFIG_PATH, "r", encoding="utf-8"))
