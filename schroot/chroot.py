from schroot.utils import run_command
from schroot.core import log
from schroot.errors import SchrootError

from contextlib import contextmanager
from tempfile import NamedTemporaryFile
import shutil
import os
import subprocess
import pipes

try:
    import configparser
except ImportError:
    import ConfigParser as configparser  # meh, Python 2


class SchrootCommandError(SchrootError):
    pass


SCHROOT_BASE = "/var/lib/schroot"


class SchrootChroot(object):
    __slots__ = ('session', 'active', 'location')

    def __init__(self):
        self.session = None
        self.active = False
        self.location = None

    def _command_prefix(self, user, preserve_environment):
        command = ['schroot', '-r', '-c', self.session]
        if user:
            command += ['-u', user]
        if preserve_environment:
            command += ['-p']
        command += ['--']
        return command

    @contextmanager
    def _command(self, cmd, kwargs):
        user = kwargs.pop("user", None)
        preserve_environment = kwargs.pop("preserve_environment", False)
        env = kwargs.pop("env", None)

        command = self._command_prefix(user, preserve_environment)

        # short cut if env not set
        if env is None:
            command += cmd
            log.debug(" ".join((str(x) for x in command)))
            yield command
            return

        tmp_dir = os.path.join(self.location, "tmp")
        with NamedTemporaryFile(dir=tmp_dir) as tmp_file:
            for key, value in env.iteritems():
                tmp_cmd = "export %s=%s" % (
                    pipes.quote(key), pipes.quote(value))
                tmp_file.write(tmp_cmd)
                tmp_file.write("\n")
            tmp_file.write('"$@"\n')
            tmp_file.flush()

            chroot_tmp_file = os.path.basename(tmp_file.name)
            chroot_tmp_file = os.path.join("/tmp", chroot_tmp_file)

            command += ['sh', '-e', chroot_tmp_file] + cmd
            log.debug(" ".join((str(x) for x in command)))
            yield command

    def _safe_run(self, cmd):
        log.debug("Command: %s" % (" ".join(cmd)))
        out, err, ret = run_command(cmd)
        if ret != 0:
            raise SchrootCommandError()
        return out, err, ret

    def copy(self, what, whence, user=None):
        with self.create_file(whence, user) as f:
            log.debug("copying %s to %s" % (what, f.name))
            with open(what) as src:
                shutil.copyfileobj(src, f)

    def get_session_config(self):
        cfg = configparser.ConfigParser()
        fil = os.path.join(SCHROOT_BASE, 'session', self.session)
        if cfg.read(fil) == []:
            raise SchrootError("SANITY FAILURE")
        return cfg[self.session]

    def start(self, chroot_name):
        out, err, ret = self._safe_run(['schroot', '-b', '-c', chroot_name])
        self.session = out.strip()
        self.active = True
        log.debug("new session: %s" % (self.session))

        out, err, ret = self._safe_run([
            'schroot', '--location', '-c', "session:%s" % self.session
        ])
        self.location = out.strip()

    def end(self):
        if self.session is not None:
            out, err, ret = self._safe_run(['schroot', '-e', '-c', self.session])

    def __lt__(self, other):
        return self.run(other, return_codes=0)

    def __floordiv__(self, other):
        return UserProxy(other, self)

    @contextmanager
    def create_file(self, whence, user=None):
        tmp_dir = os.path.join(self.location, "tmp")
        with NamedTemporaryFile(dir=tmp_dir) as tmp_file:
            chroot_tmp_file = os.path.basename(tmp_file.name)
            chroot_tmp_file = os.path.join("/tmp", chroot_tmp_file)

            log.debug("creating %s" % (tmp_file.name))
            yield tmp_file
            tmp_file.flush()
            self.check_call(['cp', chroot_tmp_file, whence], user=user)

    def run(self, cmd, **kwargs):
        with self._command(cmd, kwargs) as command:
            return run_command(command, **kwargs)

    def call(self, cmd, **kwargs):
        with self._command(cmd, kwargs) as command:
            return subprocess.call(command, **kwargs)

    def check_call(self, cmd, **kwargs):
        with self._command(cmd, kwargs) as command:
            return subprocess.check_call(command, **kwargs)

    def check_output(self, cmd, **kwargs):
        with self._command(cmd, kwargs) as command:
            return subprocess.check_output(command, **kwargs)

    def Popen(self, cmd, **kwargs):
        with self._command(cmd, kwargs) as command:
            return subprocess.Popen(command, **kwargs)


class UserProxy(SchrootChroot):
    __slots__ = ('user')

    def __init__(self, user, other):
        super(UserProxy, self).__init__()
        self.user = user
        for entry in other.__slots__:
            setattr(self, entry, getattr(other, entry))

    def run(self, cmd, return_codes=None):
        return super(UserProxy, self).run(cmd, user=self.user,
                                          return_codes=return_codes)


@contextmanager
def schroot(name):
    ch = SchrootChroot()
    try:
        ch.start(name)
        yield ch
    finally:
        ch.end()
