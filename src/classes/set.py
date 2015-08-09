from time import sleep
import os
from configparser import SafeConfigParser
from hosts import Host
from utils import get_sd_dc_objects, write_object_to_file
from ovirtsdk.xml import params


def get_iso(dc):
    for sd in dc.storagedomains.list():
        if sd.get_type() == 'iso':
            return sd.get_name()
    return False


class Set(object):
    def __init__(self, ovirtremote):
        self.api = ovirtremote.api
        self.setup = ovirtremote.setup
        self.path = ovirtremote.path
        self.hypervisor_password = self.setup['hypervisor_password']
        self.image_path = ovirtremote.image_path

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

    def get(self, string):
        if string == 'domain_state':
            return self.domain_state
        if string == 'iscsi_login':
            return self.iscsilogin
        if string == 'vm_state':
            return self.vm_state
        if string == 'host_state':
            return self.host_state
        if string == 'guestagent':
            return self.guestagent
        if string == 'operating_system':
            return self.operating_system
        if string == 'attach_disk':
            return self.attach_disk

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

    def domain_state(self, options):
        """ change domain's mode to maintainance or detach or activate """

        (sd, dc) = get_sd_dc_objects(self.api, options)
        if options.state == 'maintenance':
            try:
                sd.deactivate()
            except Exception, e:
                print e
        if options.state == 'unattached':
            while sd.get_status().get_state() != 'maintenance':
                sleep(2)
                sd = dc.storagedomains.get(options.domain)
            sd.delete()
        elif options.state == 'active':
            dc.storagedomains.add(sd)
        else:
            print "operation Failed, option: \"--state\" is needed" \
                "(maintenance, unattached, active)"
            return 1
        return 0

    def attach_disk(self, options):
        vm = self.api.vms.get(options.vm)
        if vm is None:
            print "VM %s was not found" % (options.vm)
            return 1
        disk = self.api.disks.get(options.disk)
        vm.disks.add(disk)
        sleep(2)
        disk = vm.disks.get(disk.get_name())
        disk.activate()

    def verify_host_on_cluster(self, vm, os_dest, os_info):
        host = None
        if vm.get_status().get_state() == 'up':
            host = vm.get_host()
            host = self.api.hosts.get(id=host.get_id())
        if vm.get_status().get_state() != 'down':
            vm.stop()
            sleep(4)
        if len(self.api.hosts.list()) == 1:
            host = self.api.hosts.list()[0]
        if host is None:
            vm.set_start_paused(True)
            vm.update()
            sleep(2)
            vm.start()
            vm = self.api.vms.get(name=vm.get_name())
            while vm.get_status().get_state() != 'paused':
                vm = self.api.vms.get(name=vm.get_name())
                sleep(1)
            host = vm.get_host()
            host = self.api.hosts.get(id=host.get_id())
            vm.stop()
        try:
            r_host = Host(host.get_address(), self.hypervisor_password)
        except Exception, e:
            print e
            return 1
        if not r_host.has_file(self.image_path):
            r_host.make_dir(self.image_path)
        if not r_host.has_file(os_dest['kernel']):
            self.ini_host(host, os_dest, os_info)
        vm.set_start_paused(False)
        vm.update()
        sleep(3)
        return 0

    def operating_system(self, options):
        vm = self.api.vms.get(options.vm)
        name = options.type
        os_info = self.collect_os(options.type)
        if name is None or os_info is False:
            out = os.popen('cat /etc/ovirt-remote.conf | grep "^\[[R,F].*-"')
            os_types = out.read()
            os_types = os_types.replace('\n', ' ')
            os_types = os_types.replace('[', '')
            os_types = os_types.replace(']', '')
            path = "%s/os_types" % (self.path)
            write_object_to_file(path, os_types)
            os_types = os_types.replace(' ', '\n')
            print "specify correct os type:\n%s" % (os_types)
            write_object_to_file('%s/os_types' % self.path, os_types)
            return 1
        kernel = "%s/%s%s" % (self.image_path, options.type,
                              "-x86_64-vmlinuz")
        initrd = "%s/%s%s" % (self.image_path, options.type,
                              "-x86_64-initrd.img")
        ks_path = os_info['ks']
        ks_path = ks_path.replace(' ', '%20')
        os_dest = {'name': name, 'kernel': kernel, 'initrd': initrd}
        self.verify_host_on_cluster(vm, os_dest, os_info)
        network = params.Network(name=self.api.networks.list()[0].get_name())
        nic = params.NIC(name='eth0', network=network, interface='virtio')
        if len(vm.nics.list()) == 0:
            vm.nics.add(nic)
            vm.update()
            sleep(5)
        vm = self.api.vms.get(options.vm)
        boot = params.Boot(dev='network')
        boot1 = params.Boot(dev='hd')
        str_vmlinuz = '-x86_64-vmlinuz'
        str_initrd = '-x86_64-initrd.img'
        cmdline = "%s%s initrd=boot/%s%s ks=%s" % (options.type,
                                                   str_vmlinuz,
                                                   options.type,
                                                   str_initrd,
                                                   ks_path)
        cmdline += " loglevel=debug network kssendmac noverifyssl poweroff"
        os_ = params.OperatingSystem(cmdline=cmdline, boot=[boot, boot1],
                                     initrd=initrd, kernel=kernel)
        vstart = params.VM(os=os_, run_once=True)
        action = params.Action(vm=vstart)
        vm.set_run_once(True)
        vm.update()
        vm.start(action)
        Ref = os.fork()
        if Ref == 0:
            self.engine_child(vm)
        else:
            return 0

    def vm_state(self, options):
        """ stop or start a vm """

        vm = self.api.vms.get(options.vm)
        if options.state == 'up':
            try:
                vm.start()
            except Exception, e:
                print e
        else:
            try:
                vm.stop()
            except Exception, e:
                print e

    def iscsilogin(self, options):
        """ login to iscsi session """
        if '-1' not in options.host:
            h1 = self.api.hosts.get(options.host)
        else:
            h1 = self.api.hosts.list()[0]
        iscsi = params.IscsiDetails(address=options.address,
                                    target=options.target)
        login = params.Action(iscsi=iscsi)
        h1.iscsilogin(login)

    def ini_host(self, host, os_dest, os_info):
        remote_host = Host(host.get_address(), self.hypervisor_password)
        if not remote_host.has_file(os_info['kernel']):
            remote_host.wget_file(os_dest['kernel'], os_info['kernel'])
            sleep(5)
            remote_host.wget_file(os_dest['initrd'], os_info['initrd'])
            sleep(5)

    def guestagent(self, options):
        """ install guestagent on a vm """
        ip = options.vm_address
        try:
            paramiko_vm = Host(ip, options.password)
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

    def host_state(self, options):
        """ stop or start a vm """

        h1 = self.api.hosts.get(options.host)
        if options.state == 'start':
            try:
                h1.activate()
            except Exception, e:
                print e
        else:
            try:
                h1.deactivate()
            except Exception, e:
                print e
