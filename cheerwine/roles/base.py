import inspect
from fabric import state
from fabric.api import sudo, cd
from fabric.contrib.files import exists
from ..utils import _info


class Role(object):
    """ base class for roles """

    def __init__(self, name):
        self.name = name

        for member, _ in inspect.getmembers(self, predicate=inspect.ismethod):
            if not member.startswith('_'):
                state.commands[self.name + '_' + member] = getattr(self, member)

    def _checkout(self, dirname, gitrepo, branch='master'):
        """ check code out into project directory """
        dirname = '~{}/src/{}'.format(self.name, dirname)
        if exists(dirname):
            _info('directory {} already exists'.format(dirname))
        else:
            with cd('~{}/src'.format(self.name)):
                sudo('git clone -b {} {} {}'.format(branch, gitrepo, dirname), user=self.name)

    def _update(self, dirname):
        """ update git repository """
        with cd('~{}/src/{}'.format(self.name, dirname)):
            sudo('git pull', user=self.name)
