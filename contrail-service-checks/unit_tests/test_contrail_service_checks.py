from unittest.mock import Mock
import pytest

import contrail_service_checks as csc


@pytest.fixture
def get_helper(mocker):

    config = {
        'os-credentials': '',
        'nagios_context': 'juju',
        'nagios_servicegroups': '',
        'trusted_ssl_ca': '',
        'contrail_analytics_vip': 'VIP',
    }

    helper = Mock()
    helper.store_keystone_credentials = Mock()
    helper.charm_config = config
    creds = {
        'username': 'username',
        'password': 'password',
        'region': 'region',
        'domain': 'domain',
        'auth_url': 'http://keystone:5000/v3',
        'auth_version': '3',
        'project_name': 'project'
    }
    helper.get_os_credentials = Mock(return_value=creds)
    helper.store_keystone_credentials = Mock()

    mocker.patch('contrail_service_checks.helper', helper)
    return helper


@pytest.fixture
def service(monkeypatch):
    monkeypatch.setattr(
        csc.host,
        'service_restart',
        lambda x: x
    )


@pytest.fixture
def clear_flag(mocker):
    mocker.patch('contrail_service_checks.clear_flag')


@pytest.fixture
def set_flag(mocker):
    mocker.patch('contrail_service_checks.set_flag')


@pytest.fixture
def keystone_mock():
    keystone = Mock()
    keystone.request_credentials = Mock()
    keystone.credentials_username = Mock(return_value='username')
    keystone.credentials_password = Mock(return_value='password')
    keystone.credentials_project = Mock(return_value='project')
    keystone.region = Mock(return_value='region')
    keystone.domain = Mock(return_value='domain')
    keystone.auth_protocol = Mock(return_value='http')
    keystone.auth_port = Mock(return_value='5000')
    keystone.auth_host = Mock(return_value='keystone')
    return keystone


@pytest.fixture
def status_set(mocker):
    mocker.patch('contrail_service_checks.hookenv.status_set')


@pytest.fixture
def upgrade_charm(monkeypatch):
    monkeypatch.setattr(
        csc.hookenv,
        'hook_name',
        lambda: 'upgrade-charm'
    )


@pytest.fixture
def do_reconfigure_nrpe(mocker):
    mocker.patch('contrail_service_checks.do_reconfigure_nrpe')


def test_config_changed(clear_flag):
    csc.config_changed()
    csc.clear_flag.assert_called_once_with(
        'contrail-service-checks.configured'
    )


def test_install_contrail_service_checks(clear_flag, set_flag):
    csc.install_contrail_service_checks()
    csc.set_flag.assert_called_once_with(
        'contrail-service-checks.installed'
    )
    csc.clear_flag.assert_called_once_with(
        'contrail-service-checks.configured'
    )


def test_configure_ident_username(clear_flag, keystone_mock):
    csc.configure_ident_username(keystone_mock)
    keystone_mock.request_credentials.assert_called_once_with(
        'nagios-contrail'
    )
    csc.clear_flag.assert_called_once_with(
        'contrail-service-checks.stored-creds'
    )


def test_save_creds(clear_flag, set_flag, keystone_mock, get_helper):
    csc.save_creds(keystone_mock)
    expected_creds = {
        'username': 'username',
        'password': 'password',
        'region': 'region',
        'domain': 'domain',
        'auth_url': 'http://keystone:5000/v3',
        'auth_version': '3',
        'project_name': 'project'
    }
    get_helper.store_keystone_credentials.assert_called_once_with(
        expected_creds)


def test_allow_keystone_store_overwrite(clear_flag):
    csc.allow_keystone_store_overwrite()
    csc.clear_flag.assert_called_once_with(
        'contrail-service-checks.stored-creds'
    )


def test_get_credentials(get_helper):
    result = csc.get_credentials()
    expected_creds = {
        'username': 'username',
        'password': 'password',
        'region': 'region',
        'domain': 'domain',
        'auth_url': 'http://keystone:5000/v3',
        'auth_version': '3',
        'project_name': 'project',
        'contrail_analytics_vip': 'VIP'
    }
    assert result == expected_creds


def test_render_config(get_helper, set_flag, clear_flag):
    csc.render_config()
    csc.set_flag.assert_called_once_with(
        'contrail-service-checks.configured'
    )
    csc.clear_flag.assert_called_once_with(
        'contrail-service-checks.started'
    )


def test_do_restart(set_flag, service):
    csc.do_restart()
    csc.set_flag.assert_called_once_with(
        'contrail-service-checks.started'
    )


def test_do_reconfigure_nrpe(clear_flag):
    csc.do_reconfigure_nrpe()
    csc.clear_flag.assert_called_once_with(
        'contrail-service-checks.configured'
    )


def test_missing_nrpe(status_set):
    csc.missing_nrpe()
    csc.hookenv.status_set.assert_called_once_with(
        'blocked',
        'Missing relations: nrpe'
    )


def test_upgrade_charm(upgrade_charm, do_reconfigure_nrpe):
    csc.parse_hooks()
    csc.do_reconfigure_nrpe.assert_called_once()
