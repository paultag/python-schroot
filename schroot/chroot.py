from schroot.utils import run_command
from schroot.core import log


class Chroot(object):
    session = None

    def __init__(self, chroot_name):
        out, err = safe_run(['schroot', '-b', chroot_name])
        session = self.session = out.strip()
