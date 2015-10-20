#!/usr/bin/python
from ovirtremotesdk.ovirtremote import OvirtRemote
from optparse import OptionParser
import sys
from os import system


def parseOpt(argv):
    parser = OptionParser(usage='%prog [options] "name"', version='1.22',)
    parser.add_option("--state", dest="state", default=None)
    parser.add_option("--size", dest="size", default=8)
    parser.add_option("--format", dest="format", default='raw')
    parser.add_option("--dc_version", dest="version", default=None)
    parser.add_option("--vm_address", dest="vm_address")
    parser.add_option("--diskname", dest="disk", default=None)
    parser.add_option("--sparse", dest="sparse", default=True)
    parser.add_option("--bootable", dest="bootable", default=False)
    parser.add_option("--interface", dest="interface", default='virtio')
    parser.add_option("--host", dest="host", default=None)
    parser.add_option("--hostname", dest="host", default=None)
    parser.add_option("--target", dest="target", default=None)
    parser.add_option("--vm_name", dest="vm", default=None)
    parser.add_option("--type", dest="type", default=None)
    parser.add_option("--os_type", dest="type", default=None)
    parser.add_option("--luns", dest="luns", default=None)
    parser.add_option("--path", dest="path", default=None)
    parser.add_option("--datacenter", dest="datacenter", default=None)
    parser.add_option("--cluster", dest="cluster", default=None)
    parser.add_option("--clustername", dest="cluster", default=None)
    parser.add_option("--domainname", dest="domain")
    parser.add_option("--name", dest="name")
    parser.add_option("--password", dest="password", default=None)
    parser.add_option("--address", dest="address", default=None)
    return parser.parse_args(argv)


def run_ovirt_remote(argv):
    """ This Function connects To our engine,classes and db
    """
    ovirt = OvirtRemote(argv[0], False)
    options, args = parseOpt(argv)
    if ovirt is not None:
        status = ovirt.execute_cmd(argv, options)
        if status == "successful":
            return 0
        else:
            return 1


if __name__ == "__main__":
    if sys.argv[2] == 'start_bpython':
        path = '/etc/ovirt-remote/start_bpython.py %s' % sys.argv[1]
        cmd = 'bpython -i %s' % path
        system(cmd)
    else:
        sys.exit(run_ovirt_remote(sys.argv[1:]))
