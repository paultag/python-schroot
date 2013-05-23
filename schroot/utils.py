import subprocess
import shlex


def run_command(command, stdin=None, encoding='utf-8'):
    if not isinstance(command, list):
        command = shlex.split(command)
    try:
        pipe = subprocess.Popen(command, shell=False,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
    except OSError:
        return (None, None, -1)

    kwargs = {}
    if stdin:
        kwargs['input'] = stdin.read()

    (output, stderr) = (x.decode(encoding) for x in pipe.communicate(**kwargs))
    return (output, stderr, pipe.returncode)
