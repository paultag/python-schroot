import logging


log = logging.getLogger('schroot')

def set_debug():
    log.setLevel(logging.DEBUG)
    _ch = logging.StreamHandler()
    _ch.setLevel(logging.DEBUG)
    _formatter = logging.Formatter(
        '[%(levelname)s] %(created)f: (%(funcName)s) %(message)s')
    _ch.setFormatter(_formatter)
    log.addHandler(_ch)
