import os
import time
import boto
import tempfile
from fabric.api import puts, put, hide, get, settings, prompt, env, abort, run, local, sudo
from fabric.contrib.files import exists, contains, append
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
            sudo('mkdir -p {0}'.format(remote_root), user=user)

            # copy over files
            for file in files:
                remote_file = os.path.join(remote_root, file)
                put(os.path.join(root, file), remote_file, use_sudo=True, mirror_local_mode=True)
                if user:
                    sudo('chown {0}:{0} {1}'.format(user, remote_file))


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
                res = local('diff {} {}'.format(old, filename), capture=True)
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


def is_localhost():
    if not hasattr(env, '_localhost_mode'):
        with hide('running', 'stdout'):
            run('echo ""')
        env._localhost_mode = env.host == 'localhost'
    return env._localhost_mode


def _get_ec2_metadata(type):
    with hide('running', 'stdout',  'stderr'):
        r = sudo('wget -q -O - http://169.254.169.254/latest/meta-data/{}'.format(type))
        return r


def add_ebs(size_gb, path, iops=None):
    """ add an EBS device """
    if contains('/etc/fstab', path):
        _info('/etc/fstab already contains an entry for ' + path)
        return False

    ec2 = boto.connect_ec2(env.aws_key, env.aws_secret)
    # get ec2 metadata
    zone = _get_ec2_metadata('placement/availability-zone')
    instance_id = _get_ec2_metadata('instance-id')

    # create and attach drive
    volume = ec2.create_volume(size_gb, zone, volume_type='io1' if iops else 'standard', iops=iops)

    # figure out where drive should be mounted
    letters = 'fghijklmnopqrstuvw'

    for letter in letters:
        drv = '/dev/xvd{}'.format(letter)

        # skip this letter if already mounted
        if contains('/proc/partitions', 'xvd{}'.format(letter)):
            continue

        # attach the drive, replacing xv with sd b/c of amazon quirk
        time.sleep(10)
        volume.attach(instance_id, drv.replace('xv', 's'))
        # break if we suceeded
        break
    else:
        # only executed if we didn't break
        abort('unable to mount drive')
        # TODO: ensure drive is cleaned up

    ec2.create_tags([volume.id], {'Name': '{} for {}'.format(path, instance_id)})

    _info('waiting for {}...'.format(drv))
    while not exists(drv):
        time.sleep(1)

    # format and mount the drive
    sudo('mkfs.xfs {}'.format(drv))
    append('/etc/fstab', '{0} {1} xfs defaults 0 0'.format(drv, path), use_sudo=True)

    # make & mount
    sudo('mkdir -p {}'.format(path))
    sudo('mount {}'.format(path))

    return True


def assert_configdir():
    if not getattr(env, 'configdir', None):
        _bad('config directory is not set, call production or staging')
        abort('no config directory set')
    return env.configdir
