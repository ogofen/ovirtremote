#!/usr/bin/python
from classes._ovirtremote import ovirtremote
import sys


def run(argv):
    """ This Function connects To our engine,classes and db
    """
    ovirt = ovirtremote(argv)
    return ovirt.cmd()

if __name__ == "__main__":
    sys.exit(run(sys.argv))
