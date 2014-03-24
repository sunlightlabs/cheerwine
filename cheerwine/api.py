import inspect
from fabric import state


def add_role(role_cls):
    for name, val in role_cls.__class__.__dict__.items():
        for name, _ in inspect.getmembers(role_cls, predicate=inspect.ismethod):
            if not name.startswith('_'):
                state.commands[role_cls.name + '_' + name] = getattr(role_cls, name)
