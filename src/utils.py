from optparse import OptionParser
import sys
from configparser import SafeConfigParser


def pull_sanity_options(file):
    options = dict()
    i = 0
    sanity_file = open(file, 'r')
    for line in sanity_file.readlines():
        (option, args) = parseOpt(line.split())
        options[option.domain] = option
        i = i + 1
    return options


def write_object_to_file(path, obj):
    file = open(path, 'w')
    file.write(obj)
    file.close()


def parseOpt(argv):
    parser = OptionParser(usage='%prog [options] "name"', version='1.22',)
    parser.add_option("--state", dest="state", default='1')
    parser.add_option("--size", dest="size", default='8')
    parser.add_option("--format", dest="format", default='cow')
    parser.add_option("--vm_address", dest="vm_address")
    parser.add_option("--diskname", dest="disk", default='disk')
    parser.add_option("--sparse", dest="sparse", default='True')
    parser.add_option("--bootable", dest="bootable", default='False')
    parser.add_option("--interface", dest="interface", default='virtio')
    parser.add_option("--host", dest="host", default='-1')
    parser.add_option("--target", dest="target", default='-1')
    parser.add_option("--vmname", dest="vm", default='None')
    parser.add_option("--type", dest="type", default=None)
    parser.add_option("--os_type", dest="type", default=None)
    parser.add_option("--luns", dest="luns", default='-1')
    parser.add_option("--path", dest="path", default='-1')
    parser.add_option("--datacenter", dest="datacenter", default='Default')
    parser.add_option("--cluster", dest="cluster", default='Default')
    parser.add_option("--domainname", dest="domain")
    parser.add_option("--password", dest="password", default=-1)
    parser.add_option("--address", dest="address", default='10.35.160.108')
    return parser.parse_args(argv)


def get_dc_from_cluster(api, cluster):
    for dc in api.datacenters.list():
        if dc.clusters.get(id=cluster.get_id()) is not None:
            return dc


def get_sd_dc_objects(api, options):
    sd = api.storagedomains.get(options.domain)
    try:
        dc = sd.get_data_centers().get_data_center()[0]
    except Exception:
        return sd, None
    dc = api.datacenters.get(id=dc.get_id())
    sd = dc.storagedomains.get(options.domain)
    return sd, dc


def collect_setup(setup):
    parser = SafeConfigParser()
    parser.read('/etc/ovirt-remote.conf')
    setup_dict = dict()
    try:
        setup_dict['url'] = parser.get(setup, 'url').encode('ascii')
        setup_dict['user'] = parser.get(setup, 'user').encode('ascii')
        setup_dict['password'] = parser.get(setup, 'password').encode('ascii')
        setup_dict['hypervisor_password'] = parser.get(setup,
                                                       'servers_password').encode('ascii')
        setup_dict['default_password'] = parser.get('default_password',
                                                    'password').encode('ascii')
    except Exception:
        print "setup wasn't found"
        sys.exit(1)
    return setup_dict
