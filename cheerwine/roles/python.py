import os
from fabric.api import sudo
from fabric.contrib.files import exists
from ..utils import write_configfile, jinja, add_ebs, _info
from ..server import install


class Django(object):
    def __init__(self, name, ebs_size,
                 repos, wsgi_module,
                 python3=False,
                 dependencies=None, django_settings=None, uwsgi_extras=None,
                 server_name=None, port=80, nginx_locations=None):
        self.name = name
        self.ebs_size = ebs_size
        self.repos = repos
        self.python3 = python3
        self.dependencies = dependencies or []
        self.django_settings = django_settings
        self.server_name = server_name
        self.port = port
        self.nginx_locations = nginx_locations or []

        pythonpath = [os.path.join(self.projdir, 'src', repo) for repo in self.repos]
        # log-5xx, log-slow, disable-logging, log-x-forwarded-for, reload-on-rss
        self.uwsgi_settings = {'master': 'true', 'vacuum': 'true', 'chmod-socket': '666',
                               'processes': 4,
                               'module': wsgi_module, 'pythonpath': pythonpath}
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

    def add_ebs(self):
        add_ebs(self.ebs_size, '/projects/{}'.format(self.name))
        sudo('useradd {0} --home-dir /projects/{0} --base-dir /etc/skel --shell /bin/bash'.format(
             self.name))
        # user should own their homedir
        sudo('chown {0}:{0} /projects/{0}'.format(self.name))

        sudo('mkdir -p /projects/{}/logs'.format(self.name), user=self.name)
        sudo('mkdir -p /projects/{}/src'.format(self.name),  user=self.name)
        sudo('mkdir -p /projects/{}/data'.format(self.name), user=self.name)
        sudo('mkdir -p /projects/{}/.ssh'.format(self.name), user=self.name)

    def make_venv(self):
        """ make a virtual environment """
        if self.python3:
            install(('python3', 'uwsgi-plugin-python3', 'python3-dev', 'python-virtualenv'))
        else:
            install(['uwsgi-plugin-python', 'python-dev', 'python-virtualenv'])
        dirname = '/projects/{}/virt'.format(self.name)
        if exists(dirname):
            _info('directory {} already exists'.format(dirname))
        else:
            cmd = 'virtualenv ' + dirname
            if self.python3:
                cmd += ' -p python3'
            sudo(cmd, user=self.name)

    def pip_install(self, package):
        sudo('source ~{}/virt/bin/activate && pip install {}'.format(self.name, package))

    #def django(self):
    #    """ run a django command """

    def install_server(self):
        # install both and then remove default configured site
        install(['nginx', 'uwsgi'])
        sudo('rm -f /etc/nginx/sites-enabled/default')

        # uwsgi stuff
        write_configfile('/etc/uwsgi/apps-enabled/{}.ini'.format(self.name),
                         content=self._uwsgi_ini())
        self.restart_uwsgi()

        # nginx stuff
        tmpl = jinja.get_template('nginx')
        nginx_contents = tmpl.render(port=self.port, server_name=self.server_name,
                                     locations=self.nginx.locations,
                                     project_name=self.name)
        write_configfile('/etc/nginx/sites-enabled/{}'.format(self.name),
                         content=nginx_contents)
        self.restart_nginx()

    def install_app(self):
        self.add_ebs()
        self.make_venv()
        for dirname, repo in self.repos.items():
            self.checkout(dirname, repo)

    def restart_uwsgi(self):
        sudo('/etc/init.d/uwsgi restart {0}'.format(self.name))

    def restart_nginx(self):
        sudo('/etc/init.d/nginx restart')
