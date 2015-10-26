from ovirtsdk.xml import params
from ovirtremotesdk.classes.ovirtremoteobject import remote_operation_object
from time import sleep


class New(remote_operation_object):
    def __init__(self, setup_dictionary, machine_readable):
        super(New, self).__init__(setup_dictionary, machine_readable)

    def exec_cmd(self, argv, options):
        string = argv[0]
        if string == 'fcp-domain':
            return self.blockdomain(argv[1], 'fcp',
                                    options.datacenter, options.luns)
        if string == 'iscsi-domain':
            return self.blockdomain(argv[1], 'iscsi',
                                    options.datacenter, options.luns)
        if string == 'nfs-domain':
            return self.filedomain(argv[1], 'nfs', options.datacenter,
                                   options.address, options.path)
        if string == 'vm':
            return self.vm(options.name, options.cluster)
        if string == 'openstack_volume_provider':
            return self.openstack_volume_provider(argv[1], options.datacenter)
        if string == 'disk':
            return self.disk(options.disk, options.domain, options.bootable,
                             int(options.size), options.interface,
                             options.sparse, options.format)
        if string == 'direct_lun':
            return self.direct_lun
        if string == 'iso_domain':
            return self.iso_domain(options.datacenter)
        if string == 'vm_and_bootable_disk':
            return self.vm_and_bootable_disk(options.vm, options.cluster,
                                             options.domain)
        if string == 'import_file':
            return self.importfile
        if string == 'datacenter':
            return self.datacenter(options.name, options.version)
        if string == 'cluster':
            return self.cluster(options.name, options.datacenter)
        if string == 'host':
            return self.host(argv[1], options.address, options.password,
                             options.cluster)

    def __str__(self):
        return "new"

    def get_host_and_dc(self, datacenter):
        dc = self.api.datacenters.get(datacenter)
        for host in self.api.hosts.list():
            if dc.clusters.get(id=host.get_cluster().get_id()) is not None:
                if host.get_status().get_state() == 'up':
                    return dc, host

    def host(self, host_name, address=None, password=None, cluster=None):
        """ new host"""
        if address is None:
            host_dict = self.collect_params(host_name, "hypervisors")
            address = host_dict['address']
            cluster = host_dict['cluster']
            password = host_dict['password']
        cl = self.api.clusters.get(cluster)
        host = params.Host(name=host_name, address=address,
                           cluster=cl, root_password=password)
        return self.api.hosts.add(host)

    def cluster(self, cluster, datacenter):
        """ new cluster """
        dc = self.api.datacenters.get(datacenter)
        ver = dc.get_version()
        cpu = params.CPU(id='Intel Conroe Family', architecture='X86_64')
        cl = params.Cluster(name=cluster, version=ver, data_center=dc,
                            cpu=cpu)
        return self.api.clusters.add(cl)

    def datacenter(self, datacenter, version):
        """ new datacenter """
        ver = self.api.datacenters.get('Default').get_version()
        if version is not None:
            if len(version) == 3:
                vers = version
                ver.set_major(int(vers[0]))
                ver.set_minor(int(vers[2]))
            else:
                print "wrong input for dc_version"
                return 1

        dc = params.DataCenter(name=datacenter, version=ver,
                               local=False)
        return self.api.datacenters.add(dc)

    def blockdomain(self, domain_name, type, datacenter=None, luns=None):
        """ lets create an iSCSi or fcp domain """

        (dc, host1) = self.get_host_and_dc(datacenter)
        if luns is None:
            domain_dict = self.collect_params(domain_name, "domain")
            luns = domain_dict['luns']

        storage = params.Storage(type_=type,
                                 volume_group=params.VolumeGroup(),
                                 override_luns='True')
        sd = params.StorageDomain(name=domain_name, format='True',
                                  host=host1, type_='data',
                                  storage_format='v3')
        luns_list = list()
        lun = luns
        while ',' in lun:
            id = lun[0:lun.find(',')]
            lun = lun[lun.find(',')+1:]
            luns_list.append(params.LogicalUnit(id=id))
        luns_list.append(params.LogicalUnit(id=lun))
        storage.set_logical_unit(luns_list)
        sd.set_storage(storage)
        newsd = self.api.storagedomains.add(sd)
        return dc.storagedomains.add(newsd)

    def iso_domain(self, datacenter, address, path, type):
        with open('/etc/ovirt-remote.conf', 'r') as f:
            line = f.readline()
            line = f.readline()
            address = line[line.find('=')+1:-1]
            line = f.readline()
            path = line[line.find('=')+1:-1]
        type = 'iso'
        domain = 'iso-domain'
        return self.filedomain(domain, datacenter, address, path, type)

    def direct_lun(self):
        """ create a new dlun """
        options = self.options
        luns = list()
        storage_connections = self.api.storageconnections.list()
        for connection in storage_connections:
            if connection.get_type() == options.type:
                break
        id = options.luns
        storage = params.Storage(type_=options.type)
        lun = params.LogicalUnit(id=id, address=connection.get_address(),
                                 port=3260, target=connection.get_target())
        luns.append(lun)
        storage.set_logical_unit(luns)
        disk = params.Disk(type_='data', interface=options.interface,
                           bootable=options.bootable, name=options.disk)
        disk.set_lun_storage(storage)
        return self.api.disks.add(disk)

    def disk(self, disk_name, domain_name, bootable=False, size=8,
             interface='virtio', sparse=True, format='raw', shareable=False,
             vm=None):
        """ create a new Vdisk """

        (sd, dc) = self.get_sd_dc_objects(domain_name)
        size = size*pow(1024, 3)
        disk = params.Disk(storage_domains=params.StorageDomains
                           (storage_domain=[sd]), size=size, type_='data',
                           interface=interface, format=format,
                           bootable=bootable, sparse=sparse, shareable=False,
                           name=disk_name)
        if sd.get_type() == 'volume':
            cinder = self.api.openstackvolumeproviders.list()[0]
            vol_type = cinder.volumetypes.get('ceph')
            disk.set_openstack_volume_type(vol_type)
        if vm is None:
            return self.api.disks.add(disk)
        return vm.disks.add(disk)

    def vm(self, vm_name, cluster):
        """	Build a connection string from a dictionary of parameters.Returns
        string."""

        cluster = self.api.clusters.get(cluster)
        vm_name = vm_name
        network = params.Network(name=self.api.networks.list()[0].get_name())
        nic = params.NIC(name='eth0', network=network, interface='virtio')
        vm = params.VM(name=vm_name, cluster=cluster,
                       template=self.api.templates.get(name='Blank'))
        vm = self.api.vms.add(vm)
        vm.nics.add(nic)
        vm.update()
        return vm

    def vm_and_bootable_disk(self, vm_name, cluster, domain_name):
        disk_name = vm_name + "_Disk_1"
        bootable = True
        vm = self.vm(vm_name, cluster)
        disk = self.disk(disk_name, domain_name, bootable, vm=vm)
        return vm, disk

    def importfile(self):
        options = self.options
        if '-1' not in options.host:
            host1 = self.api.hosts.get(options.host)
        else:
            host1 = self.api.hosts.list()[0]
        dc = self.api.datacenters.get(options.datacenter)
        _storage = params.Storage(type_=options.type, address=options.address,
                                  path=options.path)
        sd = params.StorageDomain(storage=_storage, host=host1, data_center=dc,
                                  type_=options._type)
        newsd = self.api.storagedomains.add(sd)
        try:
            return dc.storagedomains.add(newsd)
        except Exception, e:
            print e

    def filedomain(self, domain_name, type, datacenter, address, path):
        (dc, host1) = self.get_host_and_dc(datacenter)
        if type == 'iso':
            _type = 'iso'
            type = 'nfs'
        else:
            _type = 'data'
        if address is None and path is None:
            domain_dict = self.collect_params(domain_name, "domain")
            address = domain_dict['address']
            path = domain_dict['path']
        _storage = params.Storage
        storage = _storage(type_=type, address=address,
                           path=path)
        sd = params.StorageDomain(storage=storage, host=host1,
                                  name=domain_name, data_center=dc,
                                  type_=_type)
        newsd = self.api.storagedomains.add(sd)
        try:
            return dc.storagedomains.add(newsd)
        except Exception, e:
            print e

    def openstack_volume_provider(self, domain_name, datacenter):
        """ add cinder domain """

        dc = self.api.datacenters.get(datacenter)
        cinder = self.collect_params(domain_name, "domain")
        cinder_sd = params.OpenStackVolumeProvider
        cinder_sd = cinder_sd(name=domain_name, password=cinder['password'],
                              url=cinder['url'], username=cinder['user'],
                              authentication_url=cinder['auth_url'],
                              tenant_name=cinder['tenant'])
        cinder_sd.set_requires_authentication(True)
        self.api.openstackvolumeproviders.add(cinder_sd)
        sd = self.api.storagedomains.get(domain_name)
        dc.storagedomains.add(sd)
        sleep(5)
        cinder_sd = self.api.openstackvolumeproviders.get(domain_name)
        secret = params.OpenstackVolumeAuthenticationKey()
        secret.set_uuid(cinder['uuid'])
        secret.set_id(cinder['uuid'])
        secret.set_value(cinder['secret_value'])
        secret.set_usage_type('ceph')
        cinder_sd.authenticationkeys.add(secret)
        cinder_sd.update()
        sleep(2)
        return cinder_sd
