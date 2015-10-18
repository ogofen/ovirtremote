#!/usr/bin/python
from ovirtremotesdk.classes.delete import Delete
from ovirtremotesdk.classes.get import Get
from ovirtremotesdk.classes.new import New
from ovirtremotesdk.classes.set import Set
from ovirtremotesdk.classes.ovirtremoteobject import remote_operation_object


class OvirtRemote(remote_operation_object):
    def __init__(self, setup, machine_readable=True):
        super(OvirtRemote, self).__init__(setup, machine_readable)
        self.new = New(setup, machine_readable)
        self.delete = Delete(setup, machine_readable)
        self.get = Get(setup, machine_readable)
        self.set = Set(setup, machine_readable)
        self.operations = [self.new, self.delete, self.get, self.set]

    def getOperation(self, string):
        for func in self.operations:
            if string == func.__str__():
                return func

    def execute_cmd(self, argv, options):
        op = self.getOperation(argv[1])
        status = op.exec_cmd(argv[2:], options)
        if status == 0:
            return "successful"
