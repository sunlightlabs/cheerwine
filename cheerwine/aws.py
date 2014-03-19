"""
Amazon Web Services utilities
"""
import time
import boto
from fabric.api import hide, sudo, puts, abort, env, put, task
from fabric.contrib.files import exists, contains, append
from .utils import _info


def _get_ec2_metadata(type):
    with hide('running', 'stdout',  'stderr'):
        r = sudo('wget -q -O - http://169.254.169.254/latest/meta-data/{}'.format(type))
        return r

def add_ebs(size_gb, path, iops=None):
    """ add an EBS device """
    ec2 = boto.connect_ec2(env.AWS_KEY, env.AWS_SECRET)
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

def add_project_ebs(size, projname, iops=None):
    """ add a project EBS """
    add_ebs(size, '/projects/{}'.format(projname), iops)
    sudo('useradd {0} --home-dir /projects/{0} --base-dir /etc/skel --shell /bin/bash'.format(
         projname))
    # user should own their homedir
    sudo('chown {0}:{0} /projects/{0}'.format(projname))

    sudo('mkdir -p /projects/{}/logs'.format(projname), user=projname)
    sudo('mkdir -p /projects/{}/src'.format(projname),  user=projname)
    sudo('mkdir -p /projects/{}/data'.format(projname), user=projname)
    sudo('mkdir -p /projects/{}/.ssh'.format(projname), user=projname)
