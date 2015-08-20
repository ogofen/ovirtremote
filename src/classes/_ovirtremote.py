#!/usr/bin/python
from delete import Delete
from get import Get
from new import New
from set import Set
import sys
from utils import parseOpt, collect_params
from ovirtsdk.api import API


class ovirtremote(object):
    def __init__(self, argv):
        if len(argv) < 5:
            print "misuse of ovirt-remote tool, please refer to README file"
            sys.exit(1)
        (self.options, args) = parseOpt(argv)
        self.argv = argv
        if argv[1] == 'root':
            self.path = "/"+argv[1]+"/.ovirt-remote"
        else:
            self.path = "/home/"+argv[1]+"/.ovirt-remote"
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
        self.delete = Delete(self.api)
        self.get = Get(self)
        self.set = Set(self)
        self.operations = [self.new, self.delete, self.get, self.set]

    def getOperation(self, string):
        for func in self.operations:
            if string == func.__str__():
                return func

    def cmd(self):
        op = self.getOperation(self.argv[3])
        exe_cmd = op.get(self.argv[4])
        if exe_cmd is None:
            print "bad command or wrong syntax"
            return 1
        sys.exit(exe_cmd(self.options))
