from configparser import ConfigParser

config = ConfigParser()
config.read("config.ini")

class AppConfig:
    def __init__(self) -> None:
        app_config = config['app']
        self.host = app_config['host']
        self.port = int(app_config['port'])

