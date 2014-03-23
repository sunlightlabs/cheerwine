import os
import tempfile
from fabric.api import puts, put, hide, get, settings, prompt, env
from fabric.api import sudo as _sudo
from fabric.api import local as _local
from fabric.api import run as _run
from fabric.contrib.files import exists
from fabric.colors import red, green, cyan
from jinja2 import Environment, PackageLoader

_info = lambda x: puts(cyan(x), show_prefix=False)
_good = lambda x: puts(green(x), show_prefix=False)
_bad = lambda x: puts(red(x), show_prefix=False)


jinja = Environment(loader=PackageLoader('cheerwine', 'templates'), trim_blocks=True)


def copy_dir(local_dir, remote_dir, user=None):
    # get all files in local dir
    for root, dirs, files in os.walk(local_dir):
        # try and create directory if there are files to be put here
        if files:
            remote_root = os.path.join(remote_dir, root.replace(local_dir, ''))
            _sudo('mkdir -p {0}'.format(remote_root), user=user)

            # copy over files
            for file in files:
                remote_file = os.path.join(remote_root, file)
                put(os.path.join(root, file), remote_file, use_sudo=True, mirror_local_mode=True)
                if user:
                    _sudo('chown {0}:{0} {1}'.format(user, remote_file))


def write_configfile(remote_path, content=None, filename=None):
    _info('attempting to write {}...'.format(remote_path))

    rm_file = False
    if not filename:
        _, filename = tempfile.mkstemp()
        rm_file = True
        with open(filename, 'w') as f:
            f.write(content)

    _, old = tempfile.mkstemp()

    with hide('running', 'stdout', 'stderr'):
        if exists(remote_path):
            get(remote_path, old)
            with settings(hide('warnings'), warn_only=True):
                res = _local('diff {} {}'.format(old, filename), capture=True)
            if res.failed:
                _bad('files differ')
                puts(res, show_prefix=False)
                if prompt('update file? [y/n]') == 'y':
                    _info('writing new {}...'.format(remote_path))
                    put(filename, remote_path, use_sudo=True, mode=0644)
            else:
                _good('files already match')
        else:
            _good('no remote file exists, writing now')
            put(filename, remote_path, use_sudo=True, mode=0644)

    # remove files
    os.remove(old)
    if rm_file:
        os.remove(filename)

def cmd(cmd, sudo=None, local=getattr(env, 'CMD_LOCAL', True)):
    """ run cmd (locally unless local=False) """
    if local:
        if isinstance(sudo, str):
            _local('sudo -u {} bash -c "{}"'.format(sudo, cmd))
        elif sudo:
            _local('sudo bash -c "{}"'.format(cmd))
        else:
            _local(cmd)
    else:
        if isinstance(sudo, str):
            _sudo(cmd, user=sudo)
        elif sudo:
            _sudo(cmd)
        else:
            _run(cmd)
