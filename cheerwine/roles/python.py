import os
from fabric.api import sudo
from fabric.contrib.files import exists
from ..utils import write_configfile, jinja, add_ebs, _info
from ..server import install
from .base import Role


class Django(Role):
    def __init__(self, name, ebs_size, wsgi_module,
                 repos, files=None,
                 python3=False,
                 dependencies=None, django_settings=None, uwsgi_extras=None,
                 server_name=None, port=80, nginx_locations=None):
        super(Django, self).__init__(name)
        self.ebs_size = ebs_size
        self.repos = repos
        self.files = files
        self.python3 = python3
        self.dependencies = dependencies or []
        self.django_settings = django_settings
        self.server_name = server_name
        self.port = port
        self.nginx_locations = nginx_locations or []

        self.pythonpath = [os.path.join(self.projdir, 'src', repo) for repo in self.repos]
        # log-5xx, log-slow, disable-logging, log-x-forwarded-for, reload-on-rss
        self.uwsgi_settings = {'master': 'true', 'vacuum': 'true', 'chmod-socket': '666',
                               'processes': 4,
                               'module': wsgi_module, 'pythonpath': self.pythonpath}
        if uwsgi_extras:
            self.uwsgi_settings.update(uwsgi_extras)

    @property
    def projdir(self):
        return os.path.join('/projects', self.name)

    def _uwsgi_ini(self):
        lines = []
        for key, val in sorted(self.uwsgi_settings.items()):
            if isinstance(val, (tuple, list)):
                for item in val:
                    lines.append('{} = {}'.format(key, item))
            else:
                lines.append('{} = {}'.format(key, val))
        return jinja.get_template('uwsgi').render(user=self.name, settings=self.django_settings,
                                                  lines=lines)

    def _add_ebs(self):
        if add_ebs(self.ebs_size, '/projects/{}'.format(self.name)):
            sudo('useradd {0} --home-dir /projects/{0} --base-dir /etc/skel --shell /bin/bash'.format(
                 self.name))
            # user should own their homedir
            sudo('chown {0}:{0} /projects/{0}'.format(self.name))

            sudo('mkdir -p /projects/{}/logs'.format(self.name), user=self.name)
            sudo('mkdir -p /projects/{}/src'.format(self.name),  user=self.name)
            sudo('mkdir -p /projects/{}/data'.format(self.name), user=self.name)
            sudo('mkdir -p /projects/{}/.ssh'.format(self.name), user=self.name)

    def _make_venv(self):
        """ make a virtual environment """
        dirname = '/projects/{}/virt'.format(self.name)
        if exists(dirname):
            _info('directory {} already exists'.format(dirname))
        else:
            cmd = 'virtualenv ' + dirname
            if self.python3:
                cmd += ' -p python3'
            sudo(cmd, user=self.name)

    def _pip_install(self, package):
        """ install something into the projects virtualenv """
        sudo('source ~{}/virt/bin/activate && pip install {}'.format(self.name, package))

    def install_server(self):
        """ install the nginx and uwsgi server """
        # install both and then remove default configured site
        install(['nginx', 'uwsgi'])
        sudo('rm -f /etc/nginx/sites-enabled/default')

        # uwsgi stuff
        write_configfile('/etc/uwsgi/apps-enabled/{}.ini'.format(self.name),
                         content=self._uwsgi_ini())
        self.restart()

        # nginx stuff
        tmpl = jinja.get_template('nginx')
        nginx_contents = tmpl.render(port=self.port, server_name=self.server_name,
                                     locations=self.nginx_locations,
                                     project_name=self.name)
        write_configfile('/etc/nginx/sites-enabled/{}'.format(self.name),
                         content=nginx_contents)
        self.restart_nginx()

    def install_app(self):
        """ install the application """
        if self.python3:
            install(('python3', 'uwsgi-plugin-python3', 'python3-dev', 'python-virtualenv'))
        else:
            install(['uwsgi-plugin-python', 'python-dev', 'python-virtualenv'])
        self._add_ebs()
        self._make_venv()
        for dirname, repo in self.repos.items():
            self._checkout(dirname, repo)
        for remote, local in self.files.items():
            write_configfile(remote, filename=local)
        for dep in self.dependencies:
            if dep.startswith('-r '):
                dep = '-r ' + os.path.join('/projects', self.name, 'src', dep.split()[1])
            self._pip_install(dep)

    def logs(self):
        """ watch the logs """
        sudo('tail -f /projects/{}/logs/*'.format(self.name))

    def django(self, cmd):
        sudo('export PYTHONPATH={} && /projects/{}/virt/bin/django-admin.py {} --settings={}'.format(
             ':'.join(self.pythonpath), self.name, cmd, self.django_settings), user=self.name)

    def restart(self):
        """ restart the uwsgi process """
        sudo('/etc/init.d/uwsgi restart {}'.format(self.name))

    def restart_nginx(self):
        """ restart the nginx process """
        sudo('/etc/init.d/nginx restart')
