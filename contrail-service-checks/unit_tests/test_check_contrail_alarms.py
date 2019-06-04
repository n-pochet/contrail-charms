import pytest

import check_contrail_alarms as cca


@pytest.fixture
def keystone_client(mocker):
    mocker.patch('check_contrail_alarms.client')


def test_check_contrail_with_no_alarms(requests_mock):
    alarms = {}
    url = 'http://vip:8081/analytics/alarms'
    headers = {
        'X-Auth-Token': 'TOKEN'
    }
    requests_mock.get(url=url, headers=headers, json=alarms)
    result = cca.check_contrail_alarms('vip', 'TOKEN')
    assert result == 0


def test_check_contrail_with_alarms(requests_mock):
    alarms = {
        'config-node': [
            {
                'name': 'node08',
                'value': {
                    'UVEAlarms': {
                        'alarms': [
                            {
                                'severity': 0,
                                'timestamp': 1558601319354033,
                                'ack': False,
                                'type': 'default-global:system-connectivity',
                                'description': 'Process(es) non-functional.'
                            }
                        ],
                        '__T': 1558601342458515
                    }
                }
            }
        ],
        'vrouter': [
            {
                'name': 'node06',
                'value': {
                    'UVEAlarms': {
                        'alarms': [
                            {
                                'severity': 0,
                                'timestamp': 1558614709553302,
                                'ack': False,
                                'type': 'default-global-config:something',
                                'description': 'Node Failure.'
                            }
                        ],
                        '__T': 1558614709553864
                    }
                }
            }
        ]
    }
    url = 'http://vip:8081/analytics/alarms'
    headers = {
        'X-Auth-Token': 'TOKEN'
    }
    requests_mock.get(url=url, headers=headers, json=alarms)
    result = cca.check_contrail_alarms('vip', 'TOKEN')
    assert result == 2


def test_get_auth_token(keystone_client):
    url = 'url'
    user = 'user'
    password = 'password'
    project = 'project'
    domain = 'domain'
    cca.get_auth_token(url, user, password, project, domain)
    cca.client.Client.assert_called_once_with(
        auth_url=url,
        username=user,
        password=password,
        project_name=project,
        user_domain_name=domain,
        project_domain_name=domain
    )
