import os
import time
import glob
import json
import uuid
import ruamel.yaml

from setup_app import paths
from setup_app.static import AppType, InstallOption
from setup_app.utils import base
from setup_app.config import Config
from setup_app.utils.setup_utils import SetupUtils
from setup_app.installers.base import BaseInstaller
from setup_app.pylib.ldif4.ldif import LDIFWriter

class ConfigApiInstaller(SetupUtils, BaseInstaller):

    def __init__(self):
        self.service_name = 'jans-config-api'
        self.needdb = False # we don't need backend connection in this class
        self.app_type = AppType.SERVICE
        self.install_type = InstallOption.OPTONAL
        self.install_var = 'installConfigApi'
        self.register_progess()

        self.root_dir = os.path.join(Config.jansOptFolder, 'config-api')
        self.conf_dir = os.path.join(self.root_dir, 'config')
        self.log_dir = os.path.join(self.root_dir, 'logs')
        self.temp_dir = os.path.join(Config.templateFolder, self.service_name)

        self.uma_rs_protect_fn = os.path.join(Config.install_dir, 'setup_app/data/uma-rs-protect.json')
        self.output_folder = os.path.join(Config.outputFolder,'jans-config-api')
        self.scope_ldif_fn = os.path.join(self.output_folder, 'scopes.ldif')
        self.resources_ldif_fn = os.path.join(self.output_folder, 'resources.ldif')
        self.clients_ldif_fn = os.path.join(self.output_folder, 'clients.ldif')

        self.source_files = [
                (os.path.join(Config.distJansFolder, 'jans-config-api-runner.jar'), 'https://maven.jans.io/maven/io/jans/jans-config-api/{0}/jans-config-api-{0}-runner.jar'.format(Config.oxVersion))
                ]

    def install(self):
        self.logIt("Installing", pbar=self.service_name)

        self.copyFile(self.source_files[0][0], self.root_dir)

        self.copyFile(
                os.path.join(Config.templateFolder, self.service_name, 'application.properties'),
                self.conf_dir
                )

        self.copyFile(
                os.path.join(Config.staticFolder, 'system/initd', self.service_name),
                os.path.join(Config.distFolder, 'scripts')
                )

        self.run([paths.cmd_chmod, '+x', os.path.join(Config.distFolder, 'scripts', self.service_name)])



    def installed(self):
        return os.path.exists(self.config_api_root)


    def create_folders(self):
        for d in (self.root_dir, self.conf_dir, self.log_dir, self.output_folder):
            if not os.path.exists(d):
                self.createDirs(d)

        self.run([paths.cmd_chown, '-R', 'jetty:jetty', self.root_dir])


    def generate_configuration(self):
        uma_rs_protects = self.readFile(self.uma_rs_protect_fn)
        uma_rs_protect = json.loads(uma_rs_protects)

        self.check_clients([('jca_client_id', '1801.')])

        if not Config.get('jca_client_pw'):
            Config.jca_client_pw = self.getPW()
            Config.jca_client_encoded_pw = self.obscure(Config.jca_client_pw)

        scopes = ''
        scope_ldif_fd = open(self.scope_ldif_fn, 'wb')
        resources_ldif_fd = open(self.resources_ldif_fn, 'wb')
        ldif_scopes_writer = LDIFWriter(scope_ldif_fd, cols=1000)
        ldif_resources_writer = LDIFWriter(resources_ldif_fd, cols=1000)
        scopes = {}
        jansUmaScopes_all = []

        for resource in uma_rs_protect['resources']:

            jansUmaScopes = []

            for condition in resource['conditions']:
                for scope in condition['scopes']:
                    if not scope in scopes:
                        inum = 'CACA-' + os.urandom(2).hex().upper()
                        scope_dn = 'inum={},ou=scopes,o=jans'.format(inum)
                        scopes[scope] = {'dn': scope_dn}
                        ldif_scopes_writer.unparse(
                                scope_dn, {
                                    'objectclass': ['top', 'jansScope'],
                                    'description': ['Config API {}'.format(scope)],
                                    'displayName': ['Config API {}'.format(scope)],
                                    'inum': ['inum={}'.format(inum)],
                                    'jansDefScope': ['true'],
                                    'jansId': [scope],
                                    'jansScopeTyp': ['uma'],
                                })

                        jansUmaScopes.append(scopes[scope]['dn'])
                        jansUmaScopes_all.append(scopes[scope]['dn'])

                rid = '1800.' + str(uuid.uuid4())
                if not resource['path'].startswith('/'):
                    resource['path'] = '/' + resource['path']

                ldif_resources_writer.unparse(
                    'jansId={},ou=resources,ou=uma,o=jans'.format(rid), {
                    'displayName': ['Jans Cofig Api Uma Resource {}'.format(resource['path'])],
                    'jansAssociatedClnt': ['inum={},ou=clients,o=jans'.format(Config.jca_client_id)],
                    'jansFaviconImage': ['http://www.jans.io/img/scim_logo.png'],
                    'jansId': [rid],
                    'jansResource': ['https://{}{}'.format(Config.hostname, resource['path'])],
                    'jansUmaScope': jansUmaScopes,
                    'jansRevision': ['1'],
                    'objectClass': ['top', 'jansUmaResource'],
                    'owner': ['inum={},ou=people,o=json'.format(Config.admin_inum)]
                    })

        scope_ldif_fd.close()
        resources_ldif_fd.close()

        clients_ldif_fd = open(self.clients_ldif_fn, 'wb')
        ldif_clients_writer = LDIFWriter(clients_ldif_fd, cols=1000)
        ldif_clients_writer.unparse(
            'inum={},ou=clients,o=jans'.format(Config.jca_client_id), {
            'objectClass': ['top', 'jansClnt'],
            'del': ['false'],
            'inum': [Config.jca_client_id],
            'jansAccessTknAsJwt': ['false'],
            'jansAccessTknSigAlg': ['RS256'],
            'jansAppTyp': ['web'],
            'jansAttrs': ['{"tlsClientAuthSubjectDn":"","runIntrospectionScriptBeforeAccessTokenAsJwtCreationAndIncludeClaims":false,"keepClientAuthorizationAfterExpiration":false,"allowSpontaneousScopes":false,"spontaneousScopes":[],"spontaneousScopeScriptDns":[],"backchannelLogoutUri":[],"backchannelLogoutSessionRequired":false,"additionalAudience":[],"postAuthnScripts":[],"consentGatheringScripts":[],"introspectionScripts":[],"rptClaimsScripts":[]}'],
            'jansClntSecret': [Config.jca_client_id],
            'jansDisabled': ['false'],
            'jansGrantTyp': ['authorization_coe', 'refresh_token'],
            'jansIdTknSignedRespAlg': ['RS256'],
            'jansInclClaimsInIdTkn': ['false'],
            'jansLogoutSessRequired': ['false'],
            'jansPersistClntAuthzs': ['true'],
            'jansRequireAuthTime': ['false'],
            'jansRespTyp': ['code'],
            'jansRptAsJwt': ['false'],
            'jansScope': jansUmaScopes_all,
            'jansSubjectTyp': ['pairwise'],
            'jansTknEndpointAuthMethod': ['client_secret_basic'],
            'jansTrustedClnt': ['false'],
            })

        clients_ldif_fd.close()

    def render_import_templates(self):
        self.dbUtils.import_ldif([self.scope_ldif_fn, self.resources_ldif_fn, self.clients_ldif_fn])
