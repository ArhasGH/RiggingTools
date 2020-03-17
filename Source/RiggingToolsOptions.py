import ConfigParser
import os
import pymel.core as pm
config = ConfigParser.ConfigParser()


config_dict = {}
path = os.path.join(pm.internalVar(userAppDir=True), pm.about(v=True), "scripts/RiggingTools/config.ini")


def read_config():
    config.read(path)
    for section in config.sections():
        config_dict[section] = {}
        for option in config.options(section):
            config_dict[section][option] = config.get(section, option)


def debug_write_config(section, option, value):
    try:
        config.add_section(section)
    except ConfigParser.DuplicateSectionError:
        pass

    config.set(section, option, value)
    with open(path, "w") as f:
        config.write(f)


def write_config(section, option, value):
    config.set(section, option, value)
    with open(path, "w") as f:
        config.write(f)
