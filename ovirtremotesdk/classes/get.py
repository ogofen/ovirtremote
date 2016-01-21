from tabulate import tabulate
from hosts import Host
from ovirtremotesdk.classes.ovirtremoteobject import remote_operation_object
from ovirtsdk.xml import params


class Get(remote_operation_object):
    """ get or querry info of/on an object or field """
    def __init__(self, setup_dictionary, machine_readable):
        super(Get, self).__init__(setup_dictionary, machine_readable)

    def is_block(self, type_):
        if 'iscsi' in type_ or 'fcp' in type_:
            return True
        return False

    def __str__(self):
        return "get"

    def exec_cmd(self, argv, options):
        string = argv[0]
        if string == 'block_storage_span':
            return self.block_storage_span(argv[1], True)
        if string == 'hosts_info':
            return self.hostsinfo()
        if string == 'vms_info_list':
            return self.vms_info_list()
        if string == 'iqns_discovery':
            return self.showiqn(options.address, options.host)
        if string == 'datacenters_info':
            return self.dcinfo()
        if string == 'domains_info':
            return self.sdinfo()
        if string == 'disks_info':
            return self.disksinfo()
        if string == 'vm_ip_and_os':
            return self.vm_ip_and_os(argv[1], options.password)

    def get_unregistered(self, host, storage_list):
        used = list()
        unregistered = list()
        for storage in storage_list:
            l = storage.get_logical_unit()[0]
            if l.get_address() is not None:
                if l.get_address() not in used:
                    used.append(l.get_address())
                    iscsi = params.IscsiDetails(address=l.get_address())
                    target = [l.get_target()]
                    ac = params.Action(iscsi=iscsi, iscsi_target=target)
                    sds = host.unregisteredstoragedomainsdiscover(action=ac)
                    sd = sds.get_storage_domains().get_storage_domain()
                    unregistered.extend(sd)
        sds = host.unregisteredstoragedomainsdiscover()
        sd = sds.get_storage_domains().get_storage_domain()
        unregistered.extend(sd)
        return unregistered

    def block_storage_span(self, hostname, _print=False):
        h1 = self.api.hosts.get(hostname)
        vg_uuid_dict = dict()
        lun_uuid_list = list()
        luns_info_list = list()
        sdomains = self.api.storagedomains.list()
        storage_list = h1.storage.list()
        unsdomains = self.get_unregistered(h1, storage_list)
        for domain in sdomains:
            if self.is_block(domain.get_storage().get_type()):
                vg = domain.get_storage().get_volume_group()
                vg_uuid_dict[vg.get_id()] = domain.get_name()

        for domain in unsdomains:
            vg = domain.get_storage().get_volume_group()
            vg_uuid_dict[vg.get_id()] = domain.get_name()+'(unregistered)'

        for disk in self.api.disks.list():
            lun = disk.get_lun_storage()
            if lun is not None:
                lun_uuid_list += [lun.get_id()]

        for storage_ in storage_list:
            logical_unit = storage_.get_logical_unit()[0]
            id = storage_.get_id()
            vg_uuid = logical_unit.get_volume_group_id()
            usage = None
            lun_info = [id, vg_uuid, storage_.get_type()]
            if vg_uuid in vg_uuid_dict:
                usage = vg_uuid_dict[vg_uuid]
            if id in lun_uuid_list:
                usage = "direct lun"
            state = storage_.get_logical_unit()[0].get_status()
            size = storage_.get_logical_unit()[0].get_size()/pow(1024, 3)
            try:
                vendor = logical_unit.get_vendor_id()
            except Exception:
                vendor = "not specified"
            if usage is None:
                usage = 'available'
            lun_info += [state, size, vendor, usage]
            luns_info_list += [lun_info]
        if self.machine_readable is True:
            return luns_info_list
        table = tabulate(luns_info_list, ["id", "vg_id", "type", "status",
                                          "size", "vendor", "usage"])
        if _print is True:
            print table
            return
        return table

    def ini_host(self, host):
        password = self.collect_params(host.get_name(), 'hypervisors')['password']
        remote_host = Host(host.get_address(), password)
        src_1 = "%s/give_mac_return_ip" % (self.path)
        dest_1 = "/give_mac_return_ip"
        try:
            remote_host.put_file(src_1, dest_1)
            remote_host.run_bash_command('chmod +x %s' % dest_1)
        except Exception as e:
            print e

    def vm_ip_and_os(self, vmname, password=None):
        vm = self.api.vms.get(vmname)
        if vm is None:
            print "No VM \"%s\" was found" % (vmname)
            return 1
        cluster = vm.get_cluster()
        host = self.select_host_from_cluster(cluster.get_id())
        if password is None:
            password = self.collect_params(host.get_name(),
                                           'hypervisors')['password']
        try:
            ip = self.vm_ip(vmname, host.get_name())
        except Exception:
            print "VM \"%s\" is down or non-responsive" % vmname
            return 1
        try:
            r_vm = Host(ip, password)
        except Exception, e:
            print "Failed to open ssh session at address: %s." % (ip)
            print "Verify that guest is up and pingable from this machine.\n"
            self.write_object_to_file("vm_address", ip)
            return e
        os_info = r_vm.return_os()
        self.write_object_to_file("vm_address", ip)
        if self.machine_readable is True:
            return vm.get_name, os_info, ip
        print "VM name = \'%s\'" % vm.get_name()
        print "VM os = \'%s %s\'" % (os_info[0], os_info[1])
        print "VM ip = %s" % ip

    def vms_info_list(self):
        """ list all VM's and their ips """
        vm_info = list()
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
                mac += '%s ' % nic.get_mac().get_address()
            names = '%s %s' % (names,VM.get_name())
            vm_info.append([VM.get_name(), ip, VM.get_id(),
                            mac, VM.get_status().get_state()])

        self.write_object_to_file("vm_names", names)
        if self.machine_readable is True:
            return vm_info
        table = tabulate(vm_info, ["name", "ip", "id", "mac address", "state"])
        print table

    def disksinfo(self):
        """ list all important disks information"""
        disk_info = list()
        for disk in self.api.disks.list():
            try:
                domain = disk.get_storage_domains().get_storage_domain()[0]
                domain = self.api.storagedomains.get(id=domain.get_id())
                domain = domain.get_name()
            except Exception:
                domain = 'None'
            format = disk.get_format()
            sparse = disk.get_sparse()
            if sparse == 0:
                sparse = 'prealocated'
            elif sparse == 1:
                sparse = 'sparse'
            else:
                sparse = 'None'
            try:
                size = float(disk.get_size())/pow(1024, 3)
                size = "%.2f" % size
            except Exception:
                size = 'None'
                pass
            try:
                virtual_size = float(disk.get_provisioned_size())/pow(1024, 3)
                virtual_size = "%.2f" % virtual_size
            except Exception:
                virtual_size = 'None'
                pass
            try:
                true_size = float(disk.get_actual_size())/pow(1024, 3)
                true_size = "%.2f" % true_size
            except Exception:
                true_size = 'None'
                pass
            disk_info.append([disk.get_name(), disk.get_storage_type(),
                              format, sparse, size, virtual_size,
                              true_size, disk.get_interface(), domain])
        if self.machine_readable is True:
            return disk_info
        table = tabulate(disk_info, ["name", "type", "format", "provision",
                                     "size", "V_size(g)", "T_size(g)",
                                     "interface", "domain"])
        print table

    def hostsinfo(self):
        """ list all VM's and their ips """
        _hostsinfo = list()
        hosts_names = ''
        for host in self.api.hosts.list():
            tmp_host_info = list()
            host_name = host.get_name()
            try:
                if host.get_storage_manager().get_valueOf_() == 'true':
                    host_name += ' (spm)'
            except Exception:
                pass
            hosts_names += ''.join(host.get_name()+' ')
            tmp_host_info.append(host_name)
            tmp_host_info.append(host.get_address())
            tmp_host_info.append(host.get_id())
            tmp_host_info.append(host.get_status().get_state())
            c_id = host.get_cluster().get_id()
            cluster = self.api.clusters.get(id=c_id).get_name()
            tmp_host_info.append(cluster)
            _hostsinfo.append(tmp_host_info)
        self.write_object_to_file("hosts_names", hosts_names)
        if self.machine_readable is True:
            return _hostsinfo
        table = tabulate(_hostsinfo,
                         ["name", "address", "id", "state", "cluster"])
        print table

    def showiqn(self, address, hostname):
        """ list all host's iqns """
        h1 = self.api.hosts.get(hostname)
        iscsi = params.IscsiDetails(address=address)
        discover = params.Action(iscsi=iscsi)
        iqns = h1.iscsidiscover(discover)
        for iqn in iqns.get_iscsi_target():
            print iqn

    def dcinfo(self):
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

        self.write_object_to_file('dc_names', dc_names)
        self.write_object_to_file('cluster_names', cluster_names_)
        if self.machine_readable is True:
            return dc_info
        table = tabulate(dc_info, ["name", "cluster", "release", "id",
                                   "status"])
        print table

    def sdinfo(self):
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
        self.write_object_to_file('domain_names', domain_names)
        if self.machine_readable is True:
            return sd_info
        table = tabulate(sd_info, ["name", "type", "storage", "datacenter",
                                   "id", "status"])
        print table
