#!/usr/bin/python
from ovirtremotesdk.classes.delete import Delete
from ovirtremotesdk.classes.get import Get
from ovirtremotesdk.classes.new import New
from ovirtremotesdk.classes.set import Set
import sys
from ovirtremotesdk.utils import parseOpt, collect_params
from ovirtsdk.api import API


class ovirtremote(object):
    def __init__(self, *args):
        if len(args[0]) < 5:
            print "misuse of ovirt-remote tool, please refer to README file"
            sys.exit(1)
        argv = args[0]
        (self.options, args) = parseOpt(argv)
        self.path = "/etc/ovirt-remote"
        self.setup = collect_params(argv[2])
        try:
            self.api = API(url=self.setup['url'],
                           password=self.setup['password'],
                           username=self.setup['user'], insecure=True)
        except Exception, e:
            print e
            sys.exit(1)
        if self.options.password == -1:
            self.options.password = self.setup['default_password']
        self.image_path = '/.iso'
        self.new = New(self)
        self.delete = Delete(self)
        self.get = Get(self)
        self.set = Set(self)
        self.operations = [self.new, self.delete, self.get, self.set]

    def getOperation(self, string):
        for func in self.operations:
            if string == func.__str__():
                return func

    def cmd(self, argv):
        op = self.getOperation(argv[3])
        exe_cmd = op.get(argv[4])
        if exe_cmd is None:
            print "bad command or wrong syntax"
            return 1
        sys.exit(exe_cmd())

    def write_object_to_file(path, obj):
        file = open(path, 'w')
        file.write(obj)
        file.close()
