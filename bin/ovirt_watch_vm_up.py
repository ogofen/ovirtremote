#!/usr/bin/python
from ovirtsdk.api import API
from time import sleep
import sys


def vm_listener(api, vm_name):
    """ listen to a VM """

    sleep(90)
    vm = api.vms.get(vm_name)
    while vm.get_status().get_state() == 'up':
        sleep(1)
        vm = api.vms.get(vm_name)
    vm.stop()
    sleep(2)
    vm.start()
if __name__ == "__main__":
    u = 'https://localhost/api'
    user = 'admin@internal'
    password = sys.argv[1]
    api = API(url=u, password=password, username=user, insecure=True)
    vm_listener(api, sys.argv[2])
