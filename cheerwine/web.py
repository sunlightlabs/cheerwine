from fabric.api import sudo, env, task


def restart_nginx():
    """ restart nginx """
    sudo('/etc/init.d/nginx restart')


def restart_uwsgi():
    """ restart uwsgi """
    sudo('/etc/init.d/uwsgi restart {0}'.format(env.PROJECT_NAME))
