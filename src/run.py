#!/usr/bin/python
from ovirtremotesdk.ovirtremote import ovirtremote
from configparser import SafeConfigParser
from optparse import OptionParser
import sys
from os import system


def collect_params(setup):
    parser = SafeConfigParser()
    parser.read('/etc/ovirt-remote.conf')
    setup_dict = dict()
    try:
        setup_dict['url'] = parser.get(setup, 'url').encode('ascii')
    except Exception:
        pass
    try:
        setup_dict['cluster'] = parser.get(setup, 'cluster').encode('ascii')
    except Exception:
        pass
    try:
        setup_dict['name'] = parser.get(setup, 'name').encode('ascii')
    except Exception:
        pass
    try:
        setup_dict['user'] = parser.get(setup, 'user').encode('ascii')
    except Exception:
        pass
    try:
        setup_dict['password'] = parser.get(setup, 'password').encode('ascii')
    except Exception:
        pass
    try:
        setup_dict['secret_value'] = parser.get(setup, 'secret_value').encode('ascii')
    except Exception:
        pass
    try:
        setup_dict['uuid'] = parser.get(setup, 'uuid').encode('ascii')
    except Exception:
        pass
    try:
        setup_dict['tenant'] = parser.get(setup, 'tenant').encode('ascii')
    except Exception:
        pass
    try:
        setup_dict['auth_url'] = parser.get(setup, 'auth_url').encode('ascii')
    except Exception:
        pass
    try:
        setup_dict['hypervisor_password'] = parser.get(setup, 'servers_password').encode('ascii')
    except Exception:
        pass
    try:
        setup_dict['default_password'] = parser.get('default_password',
                                                    'password').encode('ascii')
    except Exception:
        pass
    try:
        setup_dict['password'] = parser.get(setup, 'password').encode('ascii')
    except Exception:
        pass
    try:
        setup_dict['address'] = parser.get(setup, 'address').encode('ascii')
    except Exception:
        pass
    try:
        setup_dict['path'] = parser.get(setup, 'path').encode('ascii')
    except Exception:
        pass
    try:
        setup_dict['luns'] = parser.get(setup, 'luns').encode('ascii')
    except Exception:
        pass
    return setup_dict


def parseOpt(argv):
    parser = OptionParser(usage='%prog [options] "name"', version='1.22',)
    parser.add_option("--state", dest="state", default=None)
    parser.add_option("--size", dest="size", default=None)
    parser.add_option("--format", dest="format", default=None)
    parser.add_option("--dc_version", dest="version", default=None)
    parser.add_option("--vm_address", dest="vm_address")
    parser.add_option("--diskname", dest="disk", default=None)
    parser.add_option("--sparse", dest="sparse", default=None)
    parser.add_option("--bootable", dest="bootable", default=None)
    parser.add_option("--interface", dest="interface", default=None)
    parser.add_option("--host", dest="host", default=None)
    parser.add_option("--hostname", dest="host", default=None)
    parser.add_option("--target", dest="target", default=None)
    parser.add_option("--vmname", dest="vm", default=None)
    parser.add_option("--type", dest="type", default=None)
    parser.add_option("--os_type", dest="type", default=None)
    parser.add_option("--luns", dest="luns", default=None)
    parser.add_option("--path", dest="path", default=None)
    parser.add_option("--datacenter", dest="datacenter", default=None)
    parser.add_option("--datacentername", dest="datacenter", default=None)
    parser.add_option("--cluster", dest="cluster", default=None)
    parser.add_option("--clustername", dest="cluster", default=None)
    parser.add_option("--domainname", dest="domain")
    parser.add_option("--password", dest="password", default=None)
    parser.add_option("--address", dest="address", default=None)
    return parser.parse_args(argv)


def run_ovirt_remote(argv):
    """ This Function connects To our engine,classes and db
    """
    setup_dictionary = collect_params(argv[0])
    options, args = parseOpt(argv)
    ovirt = ovirtremote(setup_dictionary, argv)
    if ovirt is not None:
        sys.exit(ovirt.execute_cmd(argv, options))

if __name__ == "__main__":
    if sys.argv[3] == 'start_bpython':
        path = '/home/%s/.ovirt-remote/start_bpython.py' % sys.argv[1]
        cmd = 'bpython -i %s %s' % (path, sys.argv[2])
        system(cmd)
    else:
        sys.exit(run_ovirt_remote(sys.argv[1:]))
