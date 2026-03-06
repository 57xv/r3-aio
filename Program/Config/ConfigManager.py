import json
import os

class ConfigManager:
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        self.default_config = {
            "threads": 50,
            "proxies_enabled": True
        }
        self.config = self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_path):
            self.save_config(self.default_config)
            return self.default_config
        
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except:
            return self.default_config

    def save_config(self, config):
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=4)
        self.config = config

    def get_setting(self, key, default=None):
        return self.config.get(key, default if default is not None else self.default_config.get(key))

    def set_setting(self, key, value):
        self.config[key] = value
        self.save_config(self.config)

config_manager = ConfigManager()
