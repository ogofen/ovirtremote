from time import sleep
import os
from configparser import SafeConfigParser
from ovirtremotesdk.classes.hosts import Host
from ovirtremotesdk.classes.ovirtremoteobject import remote_operation_object
from ovirtsdk.xml import params


class Set(remote_operation_object):
    def __init__(self, setup_dictionary, machine_readable):
        super(Set, self).__init__(setup_dictionary, machine_readable)

    def is_block(self, type_):
        if 'iscsi' in type_ or 'fcp' in type_:
            return True
        return False

    def __str__(self):
        return "set"

    def exec_cmd(self, argv, options):
        string = argv[0]
        if string == 'domain_state':
            return self.domain_state(options.domain, options.state)
        if string == 'iscsi_login':
            return self.iscsilogin(options.host, options.address,
                                   options.target)
        if string == 'vm_state':
            return self.vm_state(options.vm, options.state)
        if string == 'host_state':
            return self.host_state(options.host, options.state)
        if string == 'guestagent':
            return self.guestagent(options.vm_address, options.password)
        if string == 'operating_system':
            return self.operating_system(options.vm, argv[1])
        if string == 'attach_disk':
            return self.attach_disk(options.vm, options.disk)

    def watch_vm_up(self, vm_name):
        vm = self.api.vms.get(vm_name)
        host = vm.get_host()
        host = self.api.hosts.get(id=host.get_id())
        address = host.get_address()
        password = self.collect_params(host.get_name(),
                                       'hypervisors')['password']
        try:
            r_host = Host(address, password)
        except Exception, e:
            print e
            return 1
        path_to_file = self.path+'/ovirt_watch_vm_up.py'
        dest_path = '/root/ovirt_watch_vm_up.py'
        try:
            r_host.put_file(path_to_file, '/root/ovirt_watch_vm_up.py')
        except Exception:
            return 1
        sleep(1)
        try:
            r_host.run_bash_command('python %s %s %s' %
                                    (dest_path, password,
                                     vm.get_name()))
        except Exception:
            return 1
        return 0

    def domain_state(self, domainname, state):
        """ change domain's mode to maintainance or detach or activate """
        (sd, dc) = self.get_sd_dc_objects(domainname)
        if state == 'maintenance':
            try:
                sd.deactivate()
            except Exception, e:
                print e
        elif state == 'unattached':
            sd.deactivate()
            while sd.get_status().get_state() != 'maintenance':
                sleep(2)
                sd = dc.storagedomains.get(domainname)
            sd.delete()
        elif state == 'active':
            sd.activate()
        else:
            print "operation Failed, option: \"--state\" is needed" \
                "(maintenance, unattached, active)"
            return 1
        return 0

    def attach_disk(self, vm_name, diskname):
        vm = self.api.vms.get(vm_name)
        if vm is None:
            print "VM %s was not found" % (vm_name)
            return 1
        disk = self.api.disks.get(diskname)
        vm.disks.add(disk)
        sleep(2)
        disk = vm.disks.get(disk.get_name())
        disk.activate()

    def select_host_on_cluster(self, vm, os_dest, os_info):
        host = None
        host = vm.get_host()
        while host is None:
            if len(self.api.hosts.list()) == 1:
                host = self.api.hosts.list()[0]
                continue
            vm.start()
            sleep(4)
            vm = self.api.vms.get(name=vm.get_name())
            host = vm.get_host()
        host = self.api.hosts.get(id=host.get_id())
        try:
            print "host is %s" % host.get_name()
            password = self.collect_params(host.get_name(),
                                           'hypervisors')['password']
            r_host = Host(host.get_address(), password)
        except Exception, e:
            print e
            return 1
        if not r_host.has_file(self.image_path):
            r_host.make_dir(self.image_path)
        if not r_host.has_file(os_dest['kernel']):
            self.ini_host(host, os_dest, os_info)
        try:
            vm.stop()
        except Exception:
            pass
        while vm.get_status().get_state() != 'down':
            vm = self.api.vms.get(name=vm.get_name())
            sleep(1)
        return host

    def operating_system(self, vm_name, os_type):
        vm = self.api.vms.get(vm_name)
        os_info = self.collect_params(os_type, 'os')
        if os_type is None or os_info is False:
            print "specify correct os type"
            return 1
        kernel = "%s/%s%s" % (self.image_path, os_type,
                              "-x86_64-vmlinuz")
        initrd = "%s/%s%s" % (self.image_path, os_type,
                              "-x86_64-initrd.img")
        ks_path = os_info['ks']
        ks_path = ks_path.replace(' ', '%20')
        os_dest = {'name': os_type, 'kernel': kernel, 'initrd': initrd}
        print "preppering hypervisor for VM's os installation"
        host = self.select_host_on_cluster(vm, os_dest, os_info)
        print "hypervisor preppered"
        vm = self.api.vms.get(vm_name)
        network = params.Network(name=self.api.networks.list()[0].get_name())
        nic = params.NIC(name='eth0', network=network, interface='virtio')
        if len(vm.nics.list()) == 0:
            vm.nics.add(nic)
            vm.update()
            sleep(5)
        boot = params.Boot(dev='network')
        boot1 = params.Boot(dev='hd')
        str_vmlinuz = '-x86_64-vmlinuz'
        str_initrd = '-x86_64-initrd.img'
        cmdline = "%s%s initrd=boot/%s%s ks=%s" % (os_type,
                                                   str_vmlinuz,
                                                   os_type,
                                                   str_initrd,
                                                   ks_path)
        cmdline += " loglevel=debug network kssendmac noverifyssl poweroff"
        os_ = params.OperatingSystem(cmdline=cmdline, boot=[boot, boot1],
                                     initrd=initrd, kernel=kernel)
        vstart = params.VM(os=os_)
        action = params.Action(vm=vstart)
        vm.get_placement_policy().set_host(host)
        vm.update()

        try:
            vm.start(action)
        except Exception, e:
            print "operation failed, %s" % e
            return 1
        sleep(150)
        vm = self.api.vms.get(vm_name)
        while vm.get_status().get_state() == 'up':
            sleep(1)
            vm = self.api.vms.get(vm_name)
        vm.stop()
        vm = self.api.vms.get(vm_name)
        while vm.get_status().get_state() != 'down':
            sleep(1)
            vm = self.api.vms.get(vm_name)
        vm.start()
        return 0

    def vm_state(self, vm_name, state):
        """ stop or start a vm """

        vm = self.api.vms.get(vm_name)
        if state == 'up':
            try:
                vm.start()
            except Exception, e:
                print e
        else:
            try:
                vm.stop()
            except Exception, e:
                print e

    def iscsilogin(self, hostname, address, target):
        """ login to iscsi session """
        h1 = self.api.hosts.get(hostname)
        iscsi = params.IscsiDetails(address=address,
                                    target=target)
        login = params.Action(iscsi=iscsi)
        h1.iscsilogin(login)

    def ini_host(self, host, os_dest, os_info):
        password = self.collect_params(host.get_name(),
                                       'hypervisors')['password']
        remote_host = Host(host.get_address(), password)
        if not remote_host.has_file(os_info['kernel']):
            remote_host.wget_file(os_dest['kernel'], os_info['kernel'])
            sleep(5)
            remote_host.wget_file(os_dest['initrd'], os_info['initrd'])
            sleep(5)

    def guestagent(self, vm_address, password=None):
        """ install guestagent on a vm """
        ip = vm_address
        if password is None:
            password = 'qum5net'
        try:
            paramiko_vm = Host(ip, password)
        except Exception:
            print "ssh session failed on %s" % (ip)
        src_1 = "%s/guest.sh" % (self.path)
        dst_1 = "/root/guest.sh"
        install_guest_agent = "sh /root/guest.sh"
        paramiko_vm.put_file(src_1, dst_1)
        try:
            paramiko_vm.run_bash_command(install_guest_agent)
        except Exception as e:
            print e
            return 1
        print "guestagent has been deployed"
        return 0

    def host_state(self, hostname, state):
        """ stop or start a vm """

        h1 = self.api.hosts.get(hostname)
        if state == 'up':
            try:
                h1.activate()
            except Exception, e:
                print e
        elif state == 'maintenance':
            try:
                h1.deactivate()
            except Exception, e:
                print e
