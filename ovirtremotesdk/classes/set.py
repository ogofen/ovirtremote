from time import sleep
import sys
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

    def collect_os(self, _os):
        parser = SafeConfigParser()
        parser.read('/etc/ovirt-remote.conf')
        os_dict = dict()
        try:
            os_dict['ks'] = parser.get(_os, 'ks')
            os_dict['kernel'] = parser.get(_os, 'kernel')
            os_dict['initrd'] = parser.get(_os, 'initrd')
        except Exception:
            return False
        return os_dict

    def exec_cmd(self, string, options):
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
            return self.operating_system(options.vm, options.type)
        if string == 'attach_disk':
            return self.attach_disk(options.vm, options.disk)

    def engine_child(self, vm):
        engine_url = self.setup['url'].rstrip('/api')
        engine_url = engine_url.rsplit('https://')[1]
        try:
            r_engine = Host(engine_url, self.hypervisor_password)
        except Exception:
            return 1
        path_to_file = self.path+'/ovirt_watch_vm_up.py'
        dest_path = '/root/ovirt_watch_vm_up.py'
        try:
            r_engine.put_file(path_to_file, '/root/ovirt_watch_vm_up.py')
        except Exception:
            return 1
        sleep(1)
        try:
            r_engine.run_bash_command('python %s %s %s' %
                                      (dest_path, self.setup['password'],
                                       vm.get_name()))
        except Exception:
            return 1

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

    def attach_disk(self, vmname, diskname):
        vm = self.api.vms.get(vmname)
        if vm is None:
            print "VM %s was not found" % (vmname)
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
            r_host = Host(host.get_address(), self.hypervisor_password)
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

    def return_os_types(self):
        out = os.popen('cat /etc/ovirt-remote.conf | grep "^\[[R,F].*-"')
        os_types = out.read()
        os_types = os_types.replace('\n', ' ')
        os_types = os_types.replace('[', '')
        os_types = os_types.replace(']', '')
        self.write_object_to_file('os_types', os_types)
        return os_types.replace(' ', '\n')

    def operating_system(self, vmname, os_type):
        vm = self.api.vms.get(vmname)
        os_info = self.collect_os(os_type)
        if os_type is None or os_info is False:
            os_types = self.return_os_types()
            print "specify correct os type:\n%s" % (os_types)
            self.write_object_to_file('os_types', os_types)
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
        vm = self.api.vms.get(vmname)
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
        Ref = os.fork()
        if Ref == 0:
            print "child %s" % Ref
            sys.exit(self.engine_child(vm))
        else:
            print "father %s" % Ref
            return 0

    def vm_state(self, vmname, state):
        """ stop or start a vm """

        vm = self.api.vms.get(vmname)
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
        remote_host = Host(host.get_address(), self.hypervisor_password)
        if not remote_host.has_file(os_info['kernel']):
            remote_host.wget_file(os_dest['kernel'], os_info['kernel'])
            sleep(5)
            remote_host.wget_file(os_dest['initrd'], os_info['initrd'])
            sleep(5)

    def guestagent(self, vm_address, password=None):
        """ install guestagent on a vm """
        ip = vm_address
        if password is None:
            password = self.hypervisor_password
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
