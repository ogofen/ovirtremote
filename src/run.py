#!/usr/bin/python
from classes._ovirtremote import ovirtremote
import sys
from os import system


def run_ovirt_remote(argv):
    """ This Function connects To our engine,classes and db
    """
    ovirt = ovirtremote(argv)
    return ovirt.cmd()

if __name__ == "__main__":
    if sys.argv[3] == 'start_bpython':
        path = '/home/%s/.ovirt-remote/start_bpython.py' % sys.argv[1]
        cmd = 'bpython -i %s %s' % (path, sys.argv[2])
        system(cmd)
    else:
        sys.exit(run_ovirt_remote(sys.argv))
