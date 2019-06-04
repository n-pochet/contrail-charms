import charmhelpers
import getpass
import os
import pytest

import lib_contrail_service_checks as lcsc


@pytest.fixture
def generate_helper(monkeypatch):
    def config():
        return {
            'os-credentials': '',
            'nagios_context': 'juju',
            'nagios_servicegroups': '',
            'trusted_ssl_ca': '',
            'contrail_analytics_vip': 'VIP',
        }

    def render(source, target, context, owner, group):
        owner = getpass.getuser()
        return charmhelpers.core.templating.render(
            source,
            target,
            context,
            owner,
            owner
        )

    def relation_ids(args):
        return {}

    def makedirs(args):
        return

    def rsync(from_path, to_path, options):
        return
    monkeypatch.setattr(
        lcsc.hookenv,
        'config',
        config
    )
    monkeypatch.setattr(
        charmhelpers.contrib.charmsupport.nrpe,
        'config',
        config
    )
    monkeypatch.setattr(
        charmhelpers.contrib.charmsupport.nrpe,
        'local_unit',
        lambda: 'unit/0'
    )
    monkeypatch.setattr(
        charmhelpers.contrib.charmsupport.nrpe,
        'get_nagios_hostname',
        lambda: 'nagios'
    )
    monkeypatch.setattr(
        charmhelpers.contrib.charmsupport.nrpe,
        'relation_ids',
        relation_ids
    )
    monkeypatch.setattr(
        charmhelpers.core.hookenv,
        'charm_dir',
        lambda: '.'
    )
    monkeypatch.setattr(
        lcsc,
        'render',
        render
    )
    monkeypatch.setattr(
        os,
        'makedirs',
        makedirs
    )
    monkeypatch.setattr(
        lcsc.host,
        'rsync',
        rsync
    )
    return lcsc.CSCHelper()


def test_helper_properties(generate_helper):
    assert generate_helper.oscreds == '/var/lib/nagios/keystone.yaml'
    assert generate_helper.plugins_dir == '/usr/local/lib/nagios/plugins/'


def test_can_store_keystone_credentials(generate_helper):
    creds = {}
    generate_helper.store_keystone_credentials(creds)


def test_get_os_credentials_raises_exception_with_defaults(generate_helper):
    with pytest.raises(lcsc.CSCCredentialsError):
        generate_helper.get_os_credentials()


def test_get_os_credentials_with_missing_attributes(generate_helper):
    # Domain is missing from the credentials
    os_credentials = ('username=foo, password=bar, credentials_project=baz,'
                      ' region_name=Region1, auth_url=http://keystone:5000/v3')
    generate_helper.charm_config['os-credentials'] = os_credentials
    with pytest.raises(lcsc.CSCCredentialsError):
        generate_helper.get_os_credentials()


def test_get_os_credentials_with_v3(generate_helper):
    os_credentials = ('username=foo, password=bar, project_name=baz,'
                      ' region_name=Region1, auth_url=http://keystone:5000/v3,'
                      ' domain=domain')
    generate_helper.charm_config['os-credentials'] = os_credentials
    expected = {
        'auth_url': 'http://keystone:5000/v3',
        'project_name': 'baz',
        'username': 'foo',
        'password': 'bar',
        'domain': 'domain',
        'region_name': 'Region1'
    }
    assert generate_helper.get_os_credentials() == expected


def test_get_keystone_credentials(generate_helper):
    assert generate_helper.get_keystone_credentials() == {}


def test_render_checks(generate_helper, tmpdir, monkeypatch):
    creds = {
        'auth_url': 'http://keystone:5000/v3',
        'project_name': 'baz',
        'username': 'foo',
        'password': 'bar',
        'domain': 'domain',
        'region_name': 'Region1',
        'contrail_analytics_vip': 'vip'
    }

    oscreds = tmpdir.mkdir('oscreds').join('keystone.yaml')

    monkeypatch.setattr(
        lcsc.CSCHelper,
        'oscreds',
        property(lambda x: oscreds)
    )
    generate_helper.render_checks(creds)

    expected = ('user: foo\nproject: baz\npassword: bar\n'
                'auth_url: http://keystone:5000/v3\n'
                'domain: domain\ncontrail_analytics_vip: vip')

    with open(oscreds) as f:
        assert f.read() == expected
