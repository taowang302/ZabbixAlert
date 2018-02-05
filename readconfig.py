import configparser
class ReadConfig():
    def __init__(self, config_file, default_config={}):
        self.config_file = config_file
        self.default_config = default_config

    def read_config(self):
        config = configparser.ConfigParser()
        try:
            config.read(self.config_file)
        except UnicodeDecodeError :
            return self.default_config
        except UnicodeDecodeError :
            import codecs
            config.read_file(codecs.open("alert.conf", "r", "utf-8-sig"))
        except:
            return self.default_config
        else:
            config_dic = {}
            for section in config.sections():
                config_dic[section] = dict(config.items(section))
            return self.contrast_config(config_dic)

    def contrast_config(self, config_dic):
        if len(self.default_config):
            for key in self.default_config:
                if not config_dic.get(key):
                    config_dic[key] = self.default_config.get(key)
                else:
                    pass
        return config_dic
