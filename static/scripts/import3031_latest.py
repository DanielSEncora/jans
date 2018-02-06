#!/usr/bin/env python
"""import3031.py - Script to import the backup into Gluu Server 3.0.x

Usage: python import3031.py <path_to_backup_folder>
Example: python import3031.py /root/backup_3031

This script imports the data from backup folder generated by export3031.py.
Read complete migration procedure at:
    https://www.gluu.org/docs/deployment/upgrading/
"""

import os
import os.path
import sys
import logging
import traceback
import shutil
import json
import re
import subprocess
import time
import datetime

from distutils.dir_util import copy_tree
from ldif import LDIFParser, LDIFWriter, CreateLDIF
from jsonmerge import merge

# configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(name)s %(message)s',
                    filename='import3031.log',
                    filemode='w')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)
logging.getLogger('jsonmerge').setLevel(logging.WARNING)


class MyLDIF(LDIFParser):
    def __init__(self, input, output):
        LDIFParser.__init__(self, input)
        self.targetDN = None
        self.targetAttr = None
        self.targetEntry = None
        self.DNs = []
        self.lastDN = None
        self.lastEntry = None
        self.entries = []

    def getResults(self):
        return (self.targetDN, self.targetAttr)

    def getDNs(self):
        return self.DNs

    def getLastEntry(self):
        return self.lastEntry

    def handle(self, dn, entry):
        if self.targetDN is None:
            self.targetDN = dn
        self.lastDN = dn
        self.DNs.append(dn)
        self.entries.append(entry)
        self.lastEntry = entry
        if dn.lower().strip() == self.targetDN.lower().strip():
            self.targetEntry = entry
            if self.targetAttr in entry:
                self.targetAttr = entry[self.targetAttr]


class Migration(object):
    def __init__(self, backup):
        self.backupDir = backup
        self.ldifDir = os.path.join(backup, 'ldif')
        self.certsDir = os.path.join(backup, 'etc', 'certs')
        self.currentDir = os.path.dirname(os.path.realpath(__file__))
        self.workingDir = os.path.join(self.currentDir, 'migration')
        self.jettyDir = "/opt/gluu/jetty/"
        self.os_types = ['centos', 'redhat', 'fedora', 'ubuntu', 'debian']
        self.os = self.detect_os_type()
        self.service = "/usr/sbin/service"
        if self.os is 'centos':
            self.service = "/sbin/service"

        self.slapdConf = "/opt/symas/etc/openldap/slapd.conf"
        self.slapcat = "/opt/symas/bin/slapcat"
        self.slapadd = "/opt/symas/bin/slapadd"
        self.keytool = "/opt/jre/bin/keytool"
        self.key_store = "/opt/jre/jre/lib/security/cacerts"
        self.ldif_import = "/opt/opendj/bin/import-ldif"
        self.ldif_export = "/opt/opendj/bin/export-ldif"

        self.ldapDataFile = "/opt/gluu/data/main_db/data.mdb"
        self.ldapSiteFile = "/opt/gluu/data/site_db/data.mdb"

        self.currentData = os.path.join(self.workingDir, 'current.ldif')
        self.o_gluu = os.path.join(self.workingDir, "o_gluu.ldif")
        self.processTempFile = os.path.join(self.workingDir, "temp.ldif")
        self.o_site_static = "/install/community-edition-setup/static/cache-refresh/o_site.ldif"
        self.o_site = os.path.join(self.workingDir, "o_site.ldif")
        self.attrs = 2000
        self.objclasses = 2000
        self.ldap_type = 'openldap'
        self.gluuSchemaDir = '/opt/gluu/schema/openldap/'
        self.backupVersion = 0

        self.ox_ldap_properties = 'backup_3031/etc/gluu/conf/ox-ldap.properties'


    def readFile(self, inFilePath):
        if not os.path.exists(inFilePath):
            logging.debug("Cannot read: %s. File does not exist.", inFilePath)
            return None

        inFilePathText = None
        try:
            f = open(inFilePath)
            inFilePathText = f.read()
            f.close
        except:
            logging.warning("Error reading %s", inFilePath)
            logging.debug(traceback.format_exc())

        return inFilePathText

    def walk_function(self, a, directory, files):
        for f in files:
            fn = "%s/%s" % (directory, f)
            targetFn = fn.replace(self.backupDir, '')
            if os.path.isdir(fn):
                if not os.path.exists(targetFn):
                    os.mkdir(targetFn)
            else:
                try:
                    # if targetFn == '/etc/gluu/conf/passport-config.json':
                    #     logging.debug("Skipping %s", targetFn)
                    # elif targetFn == '/etc/certs/passport-rp.jks':
                    #     logging.debug("Skipping %s", targetFn)
                    # elif targetFn == '/etc/certs/passport-rp.pem':
                    #     logging.debug("Skipping %s", targetFn)
                    # elif targetFn == '/etc/certs/passport-rs.jkss':
                    #     logging.debug("Skipping %s", targetFn)
                    # else:
                    logging.debug("copying %s", targetFn)
                    shutil.copyfile(fn, targetFn)
                except:
                    logging.error("Error copying %s", targetFn)

    def detect_os_type(self):
        distro_info = self.readFile('/etc/redhat-release')
        if distro_info is None:
            distro_info = self.readFile('/etc/os-release')
        if 'CentOS' in distro_info:
            return self.os_types[0]
        elif 'Red Hat' in distro_info:
            return self.os_types[1]
        elif 'Ubuntu' in distro_info:
            return self.os_types[3]
        elif 'Debian' in distro_info:
            return self.os_types[4]
        else:
            return self.choose_from_list(self.os_types, "Operating System")

    def verifyBackupData(self):

        if not os.path.exists(self.backupDir):
            logging.error("Backup folder %s doesn't exist! Quitting migration",
                          self.backupDir)
            sys.exit(1)
        if not os.path.exists(self.ldifDir):
            logging.error("Backup doesn't contain directory for LDIF data."
                          " Nothing to migrate. Quitting.")
            sys.exit(1)

    def setupWorkDirectory(self):

        if not os.path.exists(self.workingDir):
            os.mkdir(self.workingDir)
        else:
            # Clean the directory in case its already present
            shutil.rmtree(self.workingDir)
            os.mkdir(self.workingDir)

    def getOutput(self, args):
        try:
            logging.debug("Running command : %s" % " ".join(args))
            p = subprocess.Popen(args, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            output, error = p.communicate()
            if error and 'Certificate was added to keystore' not in error:
                logging.error(error)
            logging.debug(output)
            return output
        except:
            logging.error("Error running command : %s" % " ".join(args))
            logging.error(traceback.format_exc())
            sys.exit(1)

    def copyCertificates(self):
        logging.info("Copying the Certificates.")
        os.path.walk("%s/etc" % self.backupDir, self.walk_function, None)

        logging.info("Updating the CA Certs Keystore.")
        keys = ['httpd', 'idp-signing', 'idp-encryption', 'shibidp', 'asimba',
                'openldap']

        # other wise gives error keytool error: java.lang.Exception: Alias <gluu.local.org_openldap> does not exist
        if self.ldap_type == 'opendj':
            keys.remove('openldap')


        hostname = self.getOutput(['hostname']).strip()
        # import all the keys into the keystore
        for key in keys:
            alias = "{0}_{1}".format(hostname, key)
            filename = os.path.join(self.certsDir, key + ".crt")
            if not os.path.isfile(filename):
                logging.debug("Missing file: %s", filename)
                continue  # skip the non-existant certs

            logging.debug('Deleting new %s', alias)
            result = self.getOutput(
                [self.keytool, '-delete', '-alias', alias, '-keystore',
                 self.key_store, '-storepass', 'changeit', '-noprompt'])
            logging.error(result) if 'error' in result else logging.debug('Delete operation success.')

            logging.debug('Importing old %s', alias)
            result = self.getOutput(
                [self.keytool, '-import', '-trustcacerts', '-file', filename,
                 '-alias', alias, '-keystore', self.key_store, '-storepass',
                 'changeit', '-noprompt'])
            logging.error(result) if 'error' in result else logging.debug('Certificate import success.')


    def stopSolserver(self):
        logging.info("Stopping OpenLDAP Server.")
        stop_msg = self.getOutput([self.service, 'solserver', 'stop'])
        output = self.getOutput([self.service, 'solserver', 'status'])
        if "is not running" in output:
            return
        else:
            logging.error("Couldn't stop the OpenLDAP server.")
            logging.error(stop_msg)
            sys.exit(1)

    def startSolserver(self):
        logging.info("Starting OpenLDAP Server.")
        start_msg = self.getOutput([self.service, 'solserver', 'start'])
        output = self.getOutput([self.service, 'solserver', 'status'])
        if "is running" in output:
            return
        else:
            logging.error("Couldn't start the OpenLDAP server.")
            logging.error(start_msg)
            sys.exit(1)

    def copyCustomFiles(self):
        logging.info("Copying the custom pages and assets of webapps.")
        folder_map = [(os.path.join(self.backupDir, 'opt'), '/opt')]

        if self.version < 300:
            custom = '/var/gluu/webapps/'
            folder_map = [
                (custom + 'oxauth/pages', self.jettyDir + 'oxauth/custom/pages'),
                (custom + 'oxauth/resources', self.jettyDir + 'oxauth/custom/static'),
                (custom + 'oxauth/libs', self.jettyDir + 'oxauth/lib/ext'),
                (custom + 'oxtrust/pages', self.jettyDir + 'identity/custom/pages'),
                (custom + 'oxtrust/resources', self.jettyDir + 'identity/custom/static'),
                (custom + 'oxtrust/libs', self.jettyDir + 'identity/lib/ext'),
            ]

        for pair in folder_map:
            copy_tree(pair[0], pair[1])

    def stopWebapps(self):
        logging.info("Stopping Webapps oxAuth and Identity.")
        #print "6 = stopWebapps oxauth and Identity"

        stop_msg = self.getOutput([self.service, 'oxauth', 'stop'])
        status = self.getOutput([self.service, 'oxauth', 'status'])
        if 'Jetty NOT running' not in status:
            logging.error("Couldn't stop oxAuth.")
            logging.error(stop_msg)

        stop_msg = self.getOutput([self.service, 'identity', 'stop'])
        status = self.getOutput([self.service, 'identity', 'status'])
        if 'Jetty NOT running' not in status:
            logging.error("Couldn't stop Identity.")
            logging.error(stop_msg)

    def startWebapps(self):
        logging.info("Starting Webapps oxAuth and Identity.")
        start_msg = self.getOutput([self.service, 'oxauth', 'start'])
        status = self.getOutput([self.service, 'oxauth', 'status'])
        if 'Jetty running pid' not in status:
            logging.error("Couldn't stop oxAuth.")
            logging.error(start_msg)

        start_msg = self.getOutput([self.service, 'identity', 'start'])
        status = self.getOutput([self.service, 'identity', 'status'])
        if 'Jetty running pid' not in status:
            logging.error("Couldn't stop Identity.")
            logging.error(start_msg)

    def exportInstallData(self):
        logging.info("Exporting LDAP data.")
        if self.ldap_type == 'openldap':
            output = self.getOutput([self.slapcat, '-f', self.slapdConf,
                                     '-l', self.currentData])
        elif self.ldap_type == 'opendj':
            output = self.getOutput(
                [self.ldif_export, '-n', 'userRoot', '-l', self.currentData])

        logging.debug(output)

    def convertSchema(self, f):
        infile = open(f, 'r')
        output = ""

        atypeRegex = re.compile('^attributeTypes:\s', re.IGNORECASE)
        obclassRegex = re.compile('^objectClasses:\s', re.IGNORECASE)

        isOCcontinue = False

        for line in infile:
            if isOCcontinue:
                if line[-1:] == ')':
                    isOCcontinue = False
                else:
                    isOCcontinue = True
                continue
            if re.match('^dn:', line) or re.match('^objectClass:', line) or \
                    re.match('^cn:', line):
                continue
            # empty lines and the comments are copied as such
            if re.match('^#', line) or re.match('^\s*$', line):
                pass
            elif re.match('^\s\s', line):  # change the space indent to tabs
                line = re.sub('^\s\s', '\t', line)
            elif re.match('^\s', line):
                line = re.sub('^\s', '\t', line)
            # Change the keyword for attributetype
            elif atypeRegex.match(line):
                line = atypeRegex.sub('\nattributetype ', line, 1)
                oid = 'oxAttribute:' + str(self.attrs + 1)
                oidregex = re.compile('\s[\d]+\s', re.IGNORECASE)
                line = oidregex.sub(' ' + oid + ' ', line, 1)
                self.attrs += 1
            # Change the keyword for objectclass
            elif obclassRegex.match(line):
                if 'SUP gluuPerson' in line and 'objectClass MAY' in line:
                    att = re.search(r'\((.*?)\)', line.split('objectClass MAY')[1]).group(1)
                    self.customAttrs.append(att)
                    continue
                elif 'SUP gluuPerson' in line and 'objectClass MUST' in line:
                    att = re.search(r'\((.*?)\)', line.split('objectClass MUST')[1]).group(1)
                    self.customAttrs.append(att)
                    continue
                else:
                    if line[-1:] == ')':
                        isOCcontinue = False
                    else:
                        isOCcontinue = True
                continue
            else:
                logging.debug("Skipping Line: {}".format(line.strip()))
                line = ""

            output += line

        infile.close()
        return output

    def updateUserSchema(self, infile, outfile):
        with open(infile, 'r') as olduser:
            with open(outfile, 'w') as newuser:
                for line in olduser:
                    if 'SUP top' in line:
                        line = line.replace('SUP top', 'SUP gluuPerson')
                    newuser.write(line)

    def copyCustomSchema(self):

        if self.ldap_type == 'openldap':

            custom_schema = os.path.join(self.gluuSchemaDir, 'custom.schema')
            outfile = open(custom_schema, 'w')
            output = self.readFile(self.backupDir + "/custom.schema")

            outfile.write("\n")
            outfile.write(output)
            outfile.close()

        else:
            return

    def getEntry(self, fn, dn):
        parser = MyLDIF(open(fn, 'rb'), sys.stdout)
        parser.targetDN = dn
        parser.parse()
        return parser.targetEntry

    def getDns(self, fn):
        parser = MyLDIF(open(fn, 'rb'), sys.stdout)
        parser.parse()
        return parser.DNs

    def getOldEntryMap(self):
        files = os.listdir(self.ldifDir)
        dnMap = {}

        # get the new admin DN
        admin_ldif = '/install/community-edition-setup/output/people.ldif'
        admin_dn = self.getDns(admin_ldif)[0]

        for fn in files:
            dnList = self.getDns(os.path.join(self.ldifDir, fn))
            for dn in dnList:
                # skip the entry of Admin DN
                if fn == 'people.ldif' and admin_dn in dn:
                    continue
                dnMap[dn] = fn
        return dnMap

    def convertTimeStamp(self, line):
        dateString = line.replace('oxAuthAuthenticationTime:', '').strip()
        try:
            dateTimestamp = time.mktime(time.strptime(dateString, "%a %b %d %H:%M:%S %Z %Y"))
            dateString = time.strftime("%Y%m%d%H%M%S", time.gmtime(dateTimestamp))
            ts = time.time()
            utc_offset = (datetime.datetime.fromtimestamp(ts) - datetime.datetime.utcfromtimestamp(ts)).total_seconds()
            dateString = "%s.%03dZ" % (
                time.strftime("%Y%m%d%H%M%S", time.localtime(dateTimestamp)), int(utc_offset // 60))
        except ValueError:
            # Data from OpenLDAP would already be in the expected format.
            # The above parsing would happen only for data from OpenDJ.
            pass
        return "%s: %s\n" % ('oxAuthAuthenticationTime', dateString)

    def processBackupData(self):
        logging.info('Processing the LDIF data.')

        processed_fp = open(self.processTempFile, 'w')
        ldif_writer = LDIFWriter(processed_fp)

        currentDNs = self.getDns(self.currentData)
        old_dn_map = self.getOldEntryMap()

        ignoreList = ['objectClass', 'ou', 'oxIDPAuthentication',
                      'gluuFreeMemory', 'gluuSystemUptime',
                      'oxLogViewerConfig', 'gluuLastUpdate']
        multivalueAttrs = ['oxTrustEmail', 'oxTrustPhoneValue', 'oxTrustImsValue',
                           'oxTrustPhotos', 'oxTrustAddresses', 'oxTrustRole',
                           'oxTrustEntitlements', 'oxTrustx509Certificate']

        if self.oxIDPAuthentication == 1:
            ignoreList.remove('oxIDPAuthentication')

        # Rewriting all the new DNs in the new installation to ldif file
        for dn in currentDNs:
            new_entry = self.getEntry(self.currentData, dn)
            if "o=site" in dn:
                continue  # skip all the o=site DNs
            if dn not in old_dn_map.keys():
                #  Write to the file if there is no matching old DN data
                ldif_writer.unparse(dn, new_entry)
                continue

            old_entry = self.getEntry(os.path.join(self.ldifDir, old_dn_map[dn]), dn)
            for attr in old_entry.keys():
                if attr in ignoreList:
                    continue

                if attr not in new_entry:
                    new_entry[attr] = old_entry[attr]
                elif old_entry[attr] != new_entry[attr]:
                    if len(old_entry[attr]) == 1:
                        try:
                            old_json = json.loads(old_entry[attr][0])
                            new_json = json.loads(new_entry[attr][0])
                            new_json = merge(new_json, old_json)
                            new_entry[attr] = [json.dumps(new_json)]
                        except:
                            if attr == 'oxScript':
                                new_entry[attr] = new_entry[attr]
                                logging.debug("Keeping new value for %s", attr)
                            else:
                                new_entry[attr] = old_entry[attr]
                                logging.debug("Keeping old value for %s", attr)
                    else:
                        new_entry[attr] = old_entry[attr]
                        logging.debug("Keep multiple old values for %s", attr)
            ldif_writer.unparse(dn, new_entry)

        # Pick all the left out DNs from the old DN map and write them to the LDIF
        for dn in sorted(old_dn_map, key=len):
            if "o=site" in dn:
                continue  # skip all the o=site DNs
            if dn in currentDNs:
                continue  # Already processed

            entry = self.getEntry(os.path.join(self.ldifDir, old_dn_map[dn]), dn)

            for attr in entry.keys():
                if attr not in multivalueAttrs:
                    continue  # skip conversion

                attr_values = []
                for val in entry[attr]:
                    json_value = None
                    try:
                        json_value = json.loads(val)
                        if type(json_value) is list:
                            attr_values.extend([json.dumps(v) for v in json_value])
                    except:
                        logging.debug('Cannot parse multival %s in DN %s', attr, dn)
                        attr_values.append(val)
                entry[attr] = attr_values

            ldif_writer.unparse(dn, entry)

        # Finally
        processed_fp.close()

        # Update the Schema change for lastModifiedTime
        with open(self.processTempFile, 'r') as infile:
            with open(self.o_gluu, 'w') as outfile:
                for line in infile:
                    line = line.replace("lastModifiedTime", "oxLastAccessTime")
                    line = line.replace('oxAuthUmaResourceSet', 'oxUmaResource')
                    if 'oxTrustAuthenticationMode' in line:
                        line = line.replace('internal', 'auth_ldap_server')
                    if 'oxAuthAuthenticationTime' in line:
                        line = self.convertTimeStamp(line)
                    if ("objectClass:" in line and line.split("objectClass: ")[1][:3] == 'ox-'):
                        line = line.replace(line, 'objectClass: gluuCustomPerson' + '\n')
                    if 'oxType' not in line and 'gluuVdsCacheRefreshLastUpdate' not in line and 'objectClass: person' not in line and 'objectClass: organizationalPerson' not in line and 'objectClass: inetOrgPerson' not in line:
                        outfile.write(line)
                    # parser = MyLDIF(open(self.currentData, 'rb'), sys.stdout)
                    # atr = parser.parse()
                    base64Types = [""]
                    # for idx, val in enumerate(parser.entries):
                    # if 'displayName' in val:
                    #     if val['displayName'][0] == 'SCIM Resource Set':
                    #         out = CreateLDIF(parser.getDNs()[idx], val,
                    #                          base64_attrs=base64Types)
                    #         f = open(self.o_gluu, "a")
                    #         f.write('\n')
                    #         f.write(out)
        data="".join(open( os.path.join(self.backupDir, 'ldif','site.ldif')).readlines()[4:-1])
        open(os.path.join(self.backupDir, 'ldif','site.ldif'),"wb").write(data)
        filenames = [self.o_site_static, os.path.join(self.backupDir, 'ldif','site.ldif')]
        with open(self.o_site, 'w') as outfile:
            for fname in filenames:
                with open(fname) as infile:
                    for line in infile:
                        outfile.write(line)
    def importDataIntoOpenldap(self):
        count = len(os.listdir('/opt/gluu/data/main_db/')) - 1
        backupfile = self.ldapDataFile + ".bkp_{0:02d}".format(count)
        logging.debug("Moving %s to %s.", self.ldapDataFile, backupfile)
        try:
            shutil.move(self.ldapDataFile, backupfile)
        except IOError:
            logging.debug(traceback.format_exc())

        count = len(os.listdir('/opt/gluu/data/site_db/')) - 1
        backupfile = self.ldapSiteFile + ".bkp_{0:02d}".format(count)
        logging.debug("Moving %s to %s.", self.ldapSiteFile, backupfile)
        try:
            shutil.move(self.ldapSiteFile, backupfile)
        except IOError:
            logging.debug(traceback.format_exc())

        output = self.getOutput([self.slapadd, '-c', '-b', 'o=gluu', '-f',
                                 self.slapdConf, '-l', self.o_gluu])
        logging.debug(output)
        output = self.getOutput([self.slapadd, '-c', '-b', 'o=site', '-f',
                                 self.slapdConf, '-l', self.o_site])
        logging.debug(output)

    def importDataIntoOpenDJ(self):

        command = [self.ldif_import,'-b','o=gluu','-n', 'userRoot',
                   '-l', self.o_gluu, '-R', self.o_gluu + '.rejects']
        output = self.getOutput(command)
        logging.debug(output)
        command = [self.ldif_import,'-b','o=gluu','-n', 'userRoot',
                   '-l', self.o_site, '-R', self.o_site + '.rejects']
        output = self.getOutput(command)
        logging.debug(output)

    def importProcessedData(self):
        logging.info("Importing Processed LDAP data.")
        if self.ldap_type == 'openldap':
            self.importDataIntoOpenldap()
        else:
            self.importDataIntoOpenDJ()



    def choice_opendj_change(self):
        # change bindDN
        if os.path.isfile(self.ox_ldap_properties):
            ox_data = ""
            try:
                with open(self.ox_ldap_properties) as f:
                    for line in f:
                        if line == 'bindDN: cn=directory manager,o=gluu\n':
                            line = 'bindDN: cn=directory manager\n'
                        ox_data += line
            except:
                logging.error(self.ox_ldap_properties+" error in reading ")
                sys.exit(0)


            fh = open(self.ox_ldap_properties, 'w')
            fh.write(ox_data)
            fh.close()

        else:
            logging.error(self.setup_properties+" File not Found")
            sys.exit(0)


    def getLDAPServerTypeChoice(self):

        try:
            choice = int(raw_input("\nChoose the target LDAP Server - 1.OpenLDAP, 2.OpenDJ [1]: "))
        except ValueError:
            logging.error("You did not enter a integer value. "
                          "Cannot decide LDAP server type. Quitting.")
            sys.exit(1)

        if choice == 1:
            self.ldap_type = 'openldap'

        elif choice == 2:
            self.ldap_type = 'opendj'
            self.choice_opendj_change()
        else:
            logging.error("Invalid selection of LDAP Server. Cannot Migrate.")
            sys.exit(1)


    def getLDAPServerType(self):
        self.oxIDPAuthentication = 2
        try:
            choice = int(raw_input(
                "\nMigrate LDAP Server details for IDP Authentication?- 1.yes, 2.no [2]: "))
        except ValueError:
            logging.error('You entered non-interger value. Cannot decide LDAP migration'
                          'server type. Quitting.')
            sys.exit(1)

        if choice == 1:
            self.oxIDPAuthentication = 1
        elif choice == 2:
            self.oxIDPAuthentication = 2
        else:
            logging.error("Invalid selection of LDAP Server. Cannot Migrate.")
            sys.exit(1)

    def stopOpenDJ(self):

        logging.info('Stopping OpenDJ Directory Server...')
        if (os.path.isfile('/usr/bin/systemctl')):
            self.getOutput(['systemctl', 'stop', 'opendj'])
            output = self.getOutput(['systemctl', 'is-active', 'opendj'])
        else:
            output = self.getOutput([self.service, 'opendj', 'stop'])

        if output.find("Directory Server is now stopped") > 0 or \
                        output.strip() == "failed":
            logging.info("Directory Server is now stopped")
        else:
            logging.error(
                "OpenDJ did not stop properly. Import cannot run without "
                "stopping the directory server. Exiting from import. Check"
                " /opt/opendj/logs/errors")
            sys.exit(1)

    def startOpenDJ(self):
        logging.info('Starting OpenDJ Directory Server...')
        if (os.path.isfile('/usr/bin/systemctl')):
            self.getOutput(['systemctl', 'start', 'opendj'])
            output = self.getOutput(['systemctl', 'is-active', 'opendj'])
        output = self.getOutput([self.service, 'opendj', 'start'])
        if output.find("Directory Server has started successfully") > 0 or \
                        output.strip() == "active":
            logging.info("Directory Server has started successfully")
        else:
            logging.error("OpenDJ did not start properly. Check "
                          "/opt/opendj/logs/errors. Restart it manually.")

    def stopLDAPServer(self):
        if self.ldap_type == 'openldap':
            self.stopSolserver()
        else:
            self.stopOpenDJ()

    def startLDAPServer(self):
        if self.ldap_type == 'openldap':
            self.startSolserver()
        else:
            self.startOpenDJ()

    def copyIDPFiles(self):
        idp_dir = os.path.join(self.backupDir, 'opt', 'idp')
        if os.path.isdir(idp_dir):
            logging.info('Copying Shibboleth IDP files...')
            if os.path.isdir(os.path.join(idp_dir, 'metadata')):
                copy_tree(
                    os.path.join(self.backupDir, 'opt', 'idp', 'metadata'),
                    '/opt/shibboleth-idp/metadata')
            if os.path.isdir(os.path.join(idp_dir, 'ssl')):
                copy_tree(
                    os.path.join(self.backupDir, 'opt', 'idp', 'ssl'),
                    '/opt/shibboleth-idp/ssl')

    def fixPermissions(self):
        logging.info('Fixing permissions for files.')

        if self.ldap_type == 'openldap':
            self.getOutput(['chown', 'ldap:ldap', self.ldapDataFile])
            self.getOutput(['chown', 'ldap:ldap', self.ldapSiteFile])

        self.getOutput(['chown','jetty:jetty',os.path.join('/opt','shibboleth-idp','metadata')])
        self.getOutput(['chown','-R','jetty:jetty',os.path.join('/opt','shibboleth-idp','conf')])

    def getProp(self, prop):
        with open(os.path.join(self.backupDir, 'setup.properties'), 'r') as f:
            for line in f:
                if line.startswith(prop):
                    return line.split('=')[-1].strip()

    def migrate(self):
        """Main function for the migration of backup data
        """
        print("\n")
        print("------------------------------------------------------------")
        print("        Gluu Server Community Edition Migration Tool        ")
        print("============================================================")
        self.version = int(self.getProp('version').replace('.', '')[0:3])
        self.getLDAPServerTypeChoice()
        self.getLDAPServerType()
        self.verifyBackupData()
        self.setupWorkDirectory()
        self.stopWebapps()
        self.stopLDAPServer()
        self.copyCertificates()
        self.copyCustomFiles()
        self.copyIDPFiles()
        self.copyCustomSchema()
        self.exportInstallData()
        self.processBackupData()
        self.importProcessedData()
        self.fixPermissions()
        self.startLDAPServer()
        # self.startWebapps()
        print("============================================================")
        print("The migration is complete. Gluu Server needs to be restarted.")
        print("\n\n\t# exit\n\t# service gluu-server-x.x.x restart\n")
        print("------------------------------------------------------------")
        print("\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "Usage: ./import3031.py <path_to_backup_folder>"
        print "Example:\n ./import3031.py /root/backup_3031"
    else:
        migrator = Migration(sys.argv[1])
        migrator.migrate()
