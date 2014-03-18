import subprocess
import shlex


def run_command(command, stdin=None, encoding='utf-8', return_codes=None,
                **kwargs):
    if not isinstance(command, list):
        command = shlex.split(command)
    try:
        pipe = subprocess.Popen(command, shell=False,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                **kwargs)
    except OSError:
        return (None, None, -1)

    kwargs = {}
    if stdin:
        kwargs['input'] = stdin.read()

    (output, stderr) = (x.decode(encoding) for x in pipe.communicate(**kwargs))

    if return_codes is not None:
        if not isinstance(return_codes, tuple):
            return_codes = (return_codes, )
        if pipe.returncode not in return_codes:
            raise SchrootCommandError("Bad return code %d" % pipe.returncode)

    return (output, stderr, pipe.returncode)
