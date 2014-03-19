import os
import tempfile
from fabric.api import puts, sudo, put, hide, get, settings, local, prompt
from fabric.contrib.files import exists
from fabric.colors import red, green, cyan
from jinja2 import Environment, PackageLoader

_info = lambda x: puts(cyan(x), show_prefix=False)
_good = lambda x: puts(green(x), show_prefix=False)
_bad = lambda x: puts(red(x), show_prefix=False)


jinja = Environment(loader=PackageLoader('cheerwine', 'templates'))


def copy_dir(local_dir, remote_dir, user=None):
    # get all files in local dir
    for root, dirs, files in os.walk(local_dir):
        # try and create directory if there are files to be put here
        if files:
            remote_root = os.path.join(remote_dir, root.replace(local_dir, ''))
            sudo('mkdir -p {0}'.format(remote_root), user=user)

            # copy over files
            for file in files:
                remote_file = os.path.join(remote_root, file)
                put(os.path.join(root, file), remote_file, use_sudo=True, mirror_local_mode=True)
                if user:
                    sudo('chown {0}:{0} {1}'.format(user, remote_file))


def write_configfile(content, remote_path):
    _, new = tempfile.mkstemp()
    _, old = tempfile.mkstemp()

    _info('checking {}...'.format(remote_path))

    with open(new, 'w') as f:
        f.write(content)
    with hide('running', 'stdout', 'stderr'):
        if exists(remote_path):
            get(remote_path, old)
            with settings(hide('warnings'), warn_only=True):
                res = local('diff {} {}'.format(old, new), capture=True)
            if res.failed:
                _bad('files differ')
                puts(res, show_prefix=False)
                if prompt('update file? [y/n]') == 'y':
                    _info('writing new {}...'.format(remote_path))
                    put(new, remote_path, use_sudo=True, mode=0644)
            else:
                _good('files already match')
        else:
            _good('no remote file exists, writing now')
            put(new, remote_path, use_sudo=True, mode=0644)

    # remove files
    os.remove(new)
    os.remove(old)
