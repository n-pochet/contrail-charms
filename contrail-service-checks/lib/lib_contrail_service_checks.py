import os

from charmhelpers.core.templating import render
from charmhelpers.contrib.openstack.utils import config_flags_parser
from charmhelpers.core import hookenv, host, unitdata
from charmhelpers.contrib.charmsupport.nrpe import NRPE


class CSCCredentialsError(Exception):
    pass


class CSCHelper():
    def __init__(self):
        self._charm_config = None

    def store_keystone_credentials(self, creds):
        '''store keystone credentials'''
        unitdata.kv().set('keystonecreds', creds)

    @property
    def charm_config(self):
        if self._charm_config is None:
            self._charm_config = hookenv.config()
        return self._charm_config

    @property
    def oscreds(self):
        return '/var/lib/nagios/keystone.yaml'

    @property
    def plugins_dir(self):
        return '/usr/local/lib/nagios/plugins/'

    def get_os_credentials(self):
        ident_creds = config_flags_parser(self.charm_config['os-credentials'])

        # Check that auth_url is in the credentials from the config
        if not ident_creds.get('auth_url'):
            raise CSCCredentialsError('auth_url')
        creds = {}
        all_attrs = ('username password region_name auth_url'
                     ' project_name domain').split()
        missing = [k for k in all_attrs if k not in ident_creds]
        # Check that there's no missing mandatory parameter
        if missing:
            raise CSCCredentialsError(', '.join(missing))

        # Strip the auth_url as it might contain quotes
        ident_creds['auth_url'] = ident_creds['auth_url'].strip('\"\'')
        creds.update(dict([(k, ident_creds.get(k)) for k in all_attrs]))

        return creds

    def get_keystone_credentials(self):
        '''retrieve keystone credentials from either config or relation data

        If config 'os-crendentials' is set, return that info,
        otherwise look for a keystonecreds relation data'

        :return: dict of credential information for keystone
        '''
        return unitdata.kv().get('keystonecreds')

    def render_checks(self, creds):
        render(source='keystone.yaml', target=self.oscreds, context=creds,
               owner='nagios', group='nagios')

        nrpe = NRPE()
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir)

        charm_plugin_dir = os.path.join(hookenv.charm_dir(),
                                        'files',
                                        'plugins/')
        host.rsync(charm_plugin_dir,
                   self.plugins_dir,
                   options=['--executability'])

        contrail_check_command = os.path.join(self.plugins_dir,
                                              'check_contrail_alarms.py')
        nrpe.add_check(shortname='contrail_alarms',
                       description='Check Contrail alarms',
                       check_cmd=contrail_check_command,
                       )

        nrpe.write()
