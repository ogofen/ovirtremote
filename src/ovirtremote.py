#!/usr/bin/python
from ovirtremotesdk.classes.delete import Delete
from ovirtremotesdk.classes.get import Get
from ovirtremotesdk.classes.new import New
from ovirtremotesdk.classes.set import Set
from ovirtremotesdk.classes.ovirtremoteobject import remoteoperationobject
from ovirtsdk.api import API
import sys


class ovirtremote(object):
    def __init__(self, setup_dictionary, argv):
        self.setup = setup_dictionary
        try:
            self.api = API(url=self.setup['url'],
                           password=self.setup['password'],
                           username=self.setup['user'], insecure=True)
        except Exception:
            print "ovirt-remote failed to connect to engine"
            sys.exit()
        remoteobject = remoteoperationobject(self, argv)
        self.new = New(remoteobject)
        self.delete = Delete(remoteobject)
        self.get = Get(remoteobject, argv)
        self.set = Set(remoteobject)
        self.operations = [self.new, self.delete, self.get, self.set]

    def getOperation(self, string):
        for func in self.operations:
            if string == func.__str__():
                return func

    def execute_cmd(self, argv, options):
        op = self.getOperation(argv[1])
        sys.exit(op.exec_cmd(argv[2], options))

    def write_object_to_file(path, obj):
        file = open(path, 'w')
        file.write(obj)
        file.close()
