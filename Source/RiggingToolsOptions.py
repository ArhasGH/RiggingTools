import ConfigParser
config = ConfigParser.ConfigParser()


def read_config(path, section, option):
    path = path.replace("Controls", "config.ini")
    config.read(path)
    return config.get(section, option)


def debug_write_config(path, section, option, value):
    path = path.replace("Controls", "config.ini")
    try:
        config.add_section(section)
    except ConfigParser.DuplicateSectionError:
        pass

    config.set(section, option, value)
    with open(path, "w") as f:
        config.write(f)


def write_config(path, section, option, value):
    path = path.replace("Controls", "config.ini")
    config.set(section, option, value)
    with open(path, "w") as f:
        config.write(f)
