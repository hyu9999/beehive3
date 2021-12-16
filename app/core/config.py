__site_configs__ = {}


def set_site_configs(site_configs):
    global __site_configs__
    __site_configs__ = site_configs
    return len(__site_configs__)


def get(name: str) -> str:
    return __site_configs__.get(name)["值"]
