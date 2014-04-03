import os
from fabric.api import env
from cheerwine.config import production, staging


def test_production():
    os.environ['CHEERWINE_CONFIG_PATH'] = os.path.join(os.path.dirname(__file__), '_configdir')
    production()
    assert env.configdir == os.environ['CHEERWINE_CONFIG_PATH']
    assert env.mode == 'production'
    assert env.secret == '123'


def test_staging():
    os.environ['CHEERWINE_CONFIG_PATH'] = os.path.join(os.path.dirname(__file__), '_configdir')
    staging()
    assert env.configdir == os.environ['CHEERWINE_CONFIG_PATH']
    assert env.mode == 'staging'
    assert env.secret == 'from staging'
