from tabulate import tabulate
from utils import write_object_to_file
from hosts import Host
from ovirtsdk.xml import params


class Get(object):
    def __init__(self, ovirtremote):
        self.api = ovirtremote.api
        self.path = ovirtremote.path
        self.setup = ovirtremote.setup
        self.hypervisor_password = self.setup['hypervisor_password']
        self.options = ovirtremote.options

    def is_block(self, type_):
        if 'iscsi' in type_ or 'fcp' in type_:
            return True
        return False

    def __str__(self):
        return "get"

    def get(self, string):
        if string == 'available_luns_info':
            return self.Available_luns_list
        if string == 'hosts_info':
            return self.hostsinfo
        if string == 'vms_info':
            return self.vmsinfo
        if string == 'iqns_discovery':
            return self.showiqn
        if string == 'datacenters_info':
            return self.dcinfo
        if string == 'domains_info':
            return self.sdinfo
        if string == 'disks_info':
            return self.disksinfo
        if string == 'vm_ip':
            return self.vm_ip
        if string == 'vm_inquiry':
            return self.vm_inquiry

    def select_host_from_cluster(self, cluster):
        for host in self.api.hosts.list():
            if host.get_cluster().get_id() == cluster:
                r_host = Host(host.get_address(), self.hypervisor_password)
                if not r_host.has_file('/give_mac_return_ip'):
                    r_host.__del__()
                    self.ini_host(host)
                return host

    def Available_luns_list(self, options):
        path = "%s/luns_id" % self.path
        luns_id = ''
        if '-1' not in options.host:
            h1 = self.api.hosts.get(options.host)
        else:
            h1 = self.api.hosts.list()[0]
        storage_list = h1.storage.list()
        luns_info_list = list()
        lun_id_list = list()
        for storage_ in storage_list:
            lun_info = list()
            lun_info.append(storage_.get_id())
            lun_info.append(storage_.get_type())
            try:
                vendor = storage_.get_logical_unit()[0].get_vendor_id()
                state = storage_.get_logical_unit()[0].get_status()
            except Exception:
                vendor = "not specified"
            lun_info.append(state)
            lun_info.append(vendor)
            luns_info_list.append(lun_info)

        if luns_info_list == []:
            print "no luns available on host"
            return 0

        print "host %s" % (h1.get_name())
        table = tabulate(luns_info_list, ["id", "type", "status", "vendor"])
        title = table.find(luns_info_list[0][0])
        for domain in self.api.storagedomains.list():
            if self.is_block(domain.get_storage().get_type()):
                print domain.get_name()
                print '-----------'
                print table[0:title-1]
                vg = domain.get_storage().get_volume_group()
                for lun in vg.get_logical_unit():
                    lun_id_list.append(lun.get_id())
                    start = table.find(lun.get_id())
                    end = start + table[start:].find('\n')
                    if end > start:
                        print table[start:end]
                    elif start == -1:
                        print "-- host can't \"see\" LUN --"
                    else:
                        print table[start:]
                print ''
            else:
                continue
        for disk in self.api.disks.list():
            lun = disk.get_lun_storage()
            if lun is not None:
                lun_id_list.append(lun.get_id())
                print ''
                print 'Direct Lun Disk %s' % (disk.get_name())
                print '-------------------'
                print table[0:title-1]
                start = table.find(lun.get_id())
                end = start + table[start:].find('\n')
                if end > start:
                    print table[start:end]
                elif start == -1:
                    print "-- host can't \"see\" LUN --"
                else:
                    print table[start:]

        print ''
        print 'Available Luns'
        print '----------------'
        print table[0:title-1]
        for storage_ in storage_list:
            if storage_.get_id() not in lun_id_list:
                start = table.find(storage_.get_id())
                luns_id += ''.join(storage_.get_id()+' ')
                end = start + table[start:].find('\n')
                if end > start:
                    print table[start:end]
                else:
                    print table[start:]
        write_object_to_file(path, luns_id)

    def vm_ip(self, options, hostname):
        vm = self.api.vms.get(options.vm)
        host = self.api.hosts.get(hostname)
        mac = vm.nics.list()[0].get_mac().get_address()
        bridge = self.api.networks.list()[0].get_name()
        try:
            r_host = Host(host.get_address(), self.hypervisor_password)
        except Exception, e:
            return e
        cmd = '/give_mac_return_ip -m %s -i %s' % (mac, bridge)
        out = r_host.run_bash_command(cmd)
        r_host.__del__()
        return out[out.find('Acquired IP:')+13:].rstrip()

    def ini_host(self, host):
        remote_host = Host(host.get_address(), self.hypervisor_password)
        src_1 = "%s/give_mac_return_ip" % (self.path)
        dest_1 = "/give_mac_return_ip"
        try:
            remote_host.put_file(src_1, dest_1)
            remote_host.run_bash_command('chmod +x %s' % dest_1)
        except Exception as e:
            print e
        remote_host.__del__()

    def vm_inquiry(self, options):
        path = "%s/vm_address" % (self.path)
        vm = self.api.vms.get(options.vm)
        if vm is None:
            print "No VM \"%s\" was found" % (options.vm)
            return 1
        cluster = vm.get_cluster()
        host = self.select_host_from_cluster(cluster.get_id())
        try:
            ip = self.vm_ip(options, host.get_name())
        except Exception:
            print "VM \"%s\" is down or non-responsive" % options.vm
            return 1
        try:
            r_vm = Host(ip, options.password)
        except Exception, e:
            print "Vm is running on %s, paramiko failed to return os" % (ip)
            write_object_to_file(path, ip)
            print e
            return e
        os_info = r_vm.return_os()
        print "VM \"%s\" is running %s %s on address: %s" % (vm.get_name(),
                                                             os_info[0],
                                                             os_info[1], ip)
        write_object_to_file(path, ip)
        r_vm.__del__()

    def vmsinfo(self, options):
        """ list all VM's and their ips """
        vm_info = list()
        path = "%s/vm_names" % (self.path)
        names = ''
        for VM in self.api.vms.list():
            ga = VM.get_guest_info()
            if ga:
                try:
                    ip = ga.ips.ip[0].get_address()
                except Exception:
                    ip = "broken ga"
            elif VM.get_status().get_state() == 'up':
                ip = 'no guest agent'
            else:
                ip = 'VM is down'
            mac = ''
            for nic in VM.nics.list():
                mac += nic.get_mac().get_address()+' '
            names = names + ' ' + VM.get_name()
            vm_info.append([VM.get_name(), ip, VM.get_id(),
                            mac, VM.get_status().get_state()])

        file = open(path, 'w')
        file.write(names)
        file.close()
        table = tabulate(vm_info, ["name", "ip", "id", "mac address", "state"])
        print table

    def disksinfo(self, options):
        """ list all VM's and their ips """
        disk_info = list()
        for disk in self.api.disks.list():
            if disk.get_name() == 'OVF_STORE':
                continue
            try:
                domain = disk.get_storage_domains().get_storage_domain()[0]
                domain = self.api.storagedomains.get(id=domain.get_id())
                domain = domain.get_name()
            except Exception:
                domain = 'None'
            vm_name = 'Floating'
            for vm in self.api.vms.list():
                if vm.disks.get(disk.get_name()):
                    vm_name = vm.get_name()
                    break
                if vm_name != 'Floating':
                    break
            if not disk.get_format():
                format = 'None'
            else:
                format = disk.get_format()
            if disk.get_bootable() is True:
                boot = 'True'
            else:
                boot = 'False'
            if disk.get_sparse() is True:
                sparse = 'sparse'
            else:
                sparse = 'preallocated'
            virtual_size = disk.get_size()/pow(1024, 3)
            true_size = disk.get_provisioned_size()/pow(1024, 3)
            disk_info.append([disk.get_name(), disk.get_storage_type(),
                              format, sparse, virtual_size, true_size,
                              disk.get_interface(), boot, domain, vm_name])
        table = tabulate(disk_info, ["name", "type", "format", "provision",
                                     "V_size(g)", "T_size(g)", "interface",
                                     "is_bootable", "domain", "vm"])
        print table

    def hostsinfo(self, options):
        """ list all VM's and their ips """
        _hostsinfo = list()
        hosts_names = ''
        path = "%s/hosts_names" % (self.path)

        for host in self.api.hosts.list():
            tmp_host_info = list()
            hosts_names += ''.join(host.get_name()+' ')
            tmp_host_info.append(host.get_name())
            tmp_host_info.append(host.get_address())
            tmp_host_info.append(host.get_id())
            tmp_host_info.append(host.get_status().get_state())
            c_id = host.get_cluster().get_id()
            cluster = self.api.clusters.get(id=c_id).get_name()
            tmp_host_info.append(cluster)
            _hostsinfo.append(tmp_host_info)
        write_object_to_file(path, hosts_names)
        table = tabulate(_hostsinfo,
                         ["name", "address", "id", "state", "cluster"])
        print table

    def showiqn(self, options):
        """ list all host's iqns """
        if '-1' not in options.host:
            h1 = self.api.hosts.get(options.host)
        else:
            print "host name is required"
            return 1
        iscsi = params.IscsiDetails(address=options.address)
        discover = params.Action(iscsi=iscsi)
        iqns = h1.iscsidiscover(discover)
        for iqn in iqns.get_iscsi_target():
            print iqn

    def dcinfo(self, options):
        """ list all dc's and their info """
        dc_info = list()
        dc_names = ''
        cluster_names_ = ' '
        for dc in self.api.datacenters.list():
            cluster_names = list()
            for cluster in dc.clusters.list():
                cluster_names.append(cluster.get_name())
            cluster_n = ", ".join(str(n) for n in cluster_names) + ' '
            cluster_names_ += cluster_n
            ver = dc.get_version()
            dc_names += ''.join(dc.get_name()+' ')
            dc_info.append([dc.get_name(), cluster_n,
                            str(ver.get_major())+'.'+str(ver.get_minor()),
                            dc.get_id(), dc.get_status().get_state()])

        table = tabulate(dc_info, ["name", "cluster", "release", "id",
                                   "status"])
        print table
        write_object_to_file('%s/dc_names' % self.path, dc_names)
        write_object_to_file('%s/cluster_names' % self.path, cluster_names_)

    def sdinfo(self, options):
        """ list all dc's and their info """
        sd_info = list()
        domain_names = ''
        for dc in self.api.datacenters.list():
            for sd in dc.storagedomains.list():
                domain_names += ''.join(sd.get_name()+' ')
                sd_name = sd.get_name()
                if sd.get_master() is True:
                    sd_name += '(master)'
                sd_info.append([sd_name, sd.get_type(),
                                sd.get_storage().get_type(), dc.get_name(),
                                sd.get_id(), sd.get_status().get_state()])
        table = tabulate(sd_info, ["name", "type", "storage", "datacenter",
                                   "id", "status"])
        for sd in self.api.storagedomains.list():
            if table.find(sd.get_name()) == -1:
                sd_name = sd.get_name()
                if sd.get_master() is True:
                    sd_name += '(master)'
                sd_info.append([sd_name, sd.get_type(),
                                sd.get_storage().get_type(), '-',
                                sd.get_id(), sd.get_status().get_state()])
        table = tabulate(sd_info, ["name", "type", "storage", "datacenter",
                                   "id", "status"])
        print table
        write_object_to_file('%s/domain_names' % (self.path), domain_names)
