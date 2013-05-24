from schroot.utils import run_command
from schroot.core import log
from schroot.errors import SchrootError

from contextlib import contextmanager


class SchrootCommandError(SchrootError):
    pass


class SchrootChroot(object):
    __slots__ = ('session', 'active')

    def __init__(self):
        self.session = None
        self.active = False

    def _safe_run(self, cmd):
        log.debug("Command: %s" % (" ".join(cmd)))
        out, err, ret = run_command(cmd)
        if ret != 0:
            raise SchrootCommandError()
        return out, err, ret

    def start(self, chroot_name):
        out, err, ret = self._safe_run(['schroot', '-b', '-c', chroot_name])
        self.session = out.strip()
        self.active = True
        log.debug("new session: %s" % (self.session))

    def end(self):
        out, err, ret = self._safe_run(['schroot', '-e', '-c', self.session])

    def run(self, cmd, user=None):
        if not isinstance(cmd, list):
            cmd = [cmd]

        command = ['schroot', '-r', '-c', self.session]
        if user:
            command += ['-u', user]
        command += ['--'] + cmd
        log.debug(" ".join((str(x) for x in command)))
        out, err, ret = run_command(command)
        return out, err, ret

    def __lt__(self, other):
        return self.run(other)

    def __floordiv__(self, other):
        return UserProxy(other, self)


class UserProxy(SchrootChroot):
    __slots__ = ('user')

    def __init__(self, user, other):
        super(UserProxy, self).__init__()
        self.user = user
        for entry in other.__slots__:
            setattr(self, entry, getattr(other, entry))

    def run(self, cmd):
        return super(UserProxy, self).run(cmd, user=self.user)


@contextmanager
def schroot(name):
    ch = SchrootChroot()
    try:
        ch.start(name)
        yield ch
    finally:
        ch.end()
