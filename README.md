# Cheerwine

a utility library for common fabric tasks

it is just a little better than [sundrop](https://github.com/sunlightlabs/sundrop)


## Public Interface

Environment Variables:

* env.PROJECT_NAME
* env.CMD_LOCAL


### cheerwine.server - General Server Utils

Commands:

* set_hosts(hostname, peers)
* add_superuser(user, directory)
* upgrade()
* install(packages)
* install_base(additional)
* checkout(dirname, gitrepo, branch='master')
* update(dirname)


### cheerwine.roles - Configuration of server into various roles


### cheerwine.utils - General Utils

Commands:

* copy_dir(local, remote, user=None)
* write_configfile(remote_path, content=None, filename=None)
* add_ebs(size_gb, path, iops=None)
