from ovirtsdk.xml import params
from ovirtremotesdk.utils import get_sd_dc_objects, collect_params
from time import sleep


class New(object):

    def __init__(self, ovirtremote):
        self.api = ovirtremote.api
        self.hypervisor_password = ovirtremote.setup['hypervisor_password']

    def exec_cmd(self, string, options):
        if string == 'fcp-domain':
            return self.blockdomain(options.domain, 'fcp',
                                    options.datacenter, options.luns)
        if string == 'iscsi-domain':
            return self.blockdomain(options.domain, 'iscsi',
                                    options.datacenter, options.luns)
        if string == 'nfs-domain':
            return self.filedomain(options.domain, 'nfs', options.datacenter,
                                   options.address, options.path)
        if string == 'vm':
            return self.vm(options.vm, options.cluster)
        if string == 'openstack_volume_provider':
            return self.openstack_volume_provider(options.datacenter)
        if string == 'disk':
            return self.disk(options.disk, options.domain, options.bootable,
                             options.type, options.size, options.sparse,
                             options.format)
        if string == 'direct_lun':
            return self.direct_lun
        if string == 'iso_domain':
            return self.iso_domain(options.datacenter)
        if string == 'vm_and_bootable_disk':
            return self.vm_and_bootable_disk(options.vm, options.cluster)
        if string == 'import_file':
            return self.importfile
        if string == 'datacenter':
            return self.datacenter(options.datacenter, options.version)
        if string == 'cluster':
            return self.cluster(options.cluster, options.datacenter)
        if string == 'host':
            return self.host(options.host, options.address, options.password,
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
            host_dict = collect_params(host_name)
            address = host_dict['address']
            cluster = host_dict['cluster']
        cl = self.api.clusters.get(cluster)
        host = params.Host(name=host_name, address=address,
                           cluster=cl, root_password=self.hypervisor_password)
        self.api.hosts.add(host)

    def cluster(self, cluster, datacenter):
        """ new cluster """
        dc = self.api.datacenters.get(datacenter)
        ver = dc.get_version()
        cpu = params.CPU(id='Intel Conroe Family', architecture='X86_64')
        cl = params.Cluster(name=cluster, version=ver, data_center=dc,
                            cpu=cpu)
        self.api.clusters.add(cl)

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
        self.api.datacenters.add(dc)

    def blockdomain(self, domain_name, type, datacenter=None, luns=None):
        """ lets create an iSCSi or fcp domain """

        (dc, host1) = self.get_host_and_dc(datacenter)
        if luns is None:
            domain_dict = collect_params(domain_name)
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
        dc.storagedomains.add(newsd)

    def iso_domain(self, datacenter, address, path, type):
        with open('/etc/ovirt-remote.conf', 'r') as f:
            line = f.readline()
            line = f.readline()
            address = line[line.find('=')+1:-1]
            line = f.readline()
            path = line[line.find('=')+1:-1]
        type = 'iso'
        domain = 'iso-domain'
        self.filedomain(domain, datacenter, address, path, type)

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
        self.api.disks.add(disk)

    def disk(self, disk_name, domain_name, bootable=False, size=8,
             interface='virtio', sparse=True, format='raw'):
        """ create a new Vdisk """

        (sd, dc) = get_sd_dc_objects(self.api, domain_name)
        dc = self.api.datacenters.get(id=dc.get_id())
        sd = dc.storagedomains.get(domain_name)
        size = size*pow(1024, 3)
        disk = params.Disk(storage_domains=params.StorageDomains
                           (storage_domain=[sd]), size=size, type_='data',
                           interface=interface, format=format,
                           bootable=bootable, sparse=sparse,
                           name=disk_name)
        if sd.get_type() == 'volume':
            cinder = self.api.openstackvolumeproviders.get('cinder')
            vol_type = cinder.volumetypes.get('ceph')
            disk.set_openstack_volume_type(vol_type)
        self.api.disks.add(disk)
        sleep(5)

    def vm(self, vm_name, cluster):
        """	Build a connection string from a dictionary of parameters.Returns
        string."""

        cluster = self.api.clusters.get(cluster)
        vm_name = vm_name
        network = params.Network(name=self.api.networks.list()[0].get_name())
        nic = params.NIC(name='eth0', network=network, interface='virtio')
        vm = params.VM(name=vm_name, cluster=cluster,
                       template=self.api.templates.get(name='Blank'))
        self.api.vms.add(vm)
        vm = self.api.vms.get(vm_name)
        vm.nics.add(nic)
        vm.update()
        return 0

    def vm_and_bootable_disk(self, vm_name, cluster, domain_name):
        disk_name = vm_name + "_Disk_1"
        bootable = True
        self.vm(vm_name, cluster)
        self.disk(disk_name, domain_name, bootable)
        sleep(5)
        sd = self.api.storagedomains.get(domain_name)
        vm = self.api.vms.get(vm_name)
        disk = sd.disks.get(disk_name)
        vm.disks.add(disk_name)
        sleep(2)
        disk = vm.disks.get(disk.get_name())
        disk.activate()

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
            dc.storagedomains.add(newsd)
        except Exception, e:
            print e

    def filedomain(self, domain_name, type, datacenter, address, path):
        (dc, host1) = self.get_host_and_dc(datacenter)
        if type == 'iso':
            _type = 'iso'
            type = 'nfs'
        else:
            _type = 'data'
        if address == '-1' and path == '-1':
            domain_dict = collect_params(domain_name)
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
            dc.storagedomains.add(newsd)
        except Exception, e:
            print e

    def openstack_volume_provider(self):
        """ add cinder domain """

        options = self.options
        dc = self.api.datacenters.get(options.datacenter)
        cinder = collect_params('openstack_volume_provider')
        cinder_sd = params.OpenStackVolumeProvider
        cinder_sd = cinder_sd(name=cinder['name'], password=cinder['password'],
                              url=cinder['url'], username=cinder['user'],
                              authentication_url=cinder['auth_url'],
                              tenant_name=cinder['tenant'])
        cinder_sd.set_requires_authentication(True)
        self.api.openstackvolumeproviders.add(cinder_sd)
        sd = self.api.storagedomains.get(cinder['name'])
        dc.storagedomains.add(sd)
        sleep(5)
        cinder_sd = self.api.openstackvolumeproviders.get(cinder['name'])
        secret = params.OpenstackVolumeAuthenticationKey()
        secret.set_uuid(cinder['uuid'])
        secret.set_id(cinder['uuid'])
        secret.set_value(cinder['secret_value'])
        secret.set_usage_type('ceph')
        cinder_sd.authenticationkeys.add(secret)
