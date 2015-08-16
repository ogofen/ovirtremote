from ovirtsdk.xml import params
from utils import get_sd_dc_objects, collect_params
from time import sleep


class New(object):

    def __init__(self, ovirtremote):
        self.api = ovirtremote.api
        self.options = ovirtremote.options

    def get(self, string):
        if string == 'fcp-domain':
            self.options.type = 'fcp'
            return self.blockdomain
        if string == 'iscsi-domain':
            self.options.type = 'iscsi'
            return self.blockdomain
        if string == 'nfs-domain':
            self.options.type = 'nfs'
            return self.filedomain
        if string == 'vm':
            return self.vm
        if string == 'openstack_volume_provider':
            return self.openstack_volume_provider
        if string == 'disk':
            return self.disk
        if string == 'direct_lun':
            return self.direct_lun
        if string == 'iso_domain':
            return self.iso_domain
        if string == 'vm_and_bootable_disk':
            return self.vm_and_bootable_disk
        if string == 'import_file':
            return self.importfile

    def __str__(self):
        return "new"

    def get_host_and_dc(self, options):
        dc = self.api.datacenters.get(options.datacenter)
        for host in self.api.hosts.list():
            if dc.clusters.get(id=host.get_cluster().get_id()) is not None:
                return dc, host

    def blockdomain(self, options):
        """ lets create an iSCSI domain """

        if '-1' not in options.host:
            host1 = self.api.hosts.get(options.host)
        else:
            (dc, host1) = self.get_host_and_dc(options)
        if options.luns == '-1':
            domain_dict = collect_params(options.domain)
            options.luns = domain_dict['luns']

        luns = list()
        storage = params.Storage(type_=options.type,
                                 volume_group=params.VolumeGroup(),
                                 override_luns='True')
        sd = params.StorageDomain(name=options.domain, format='True',
                                  host=host1, type_='data',
                                  storage_format='v3')
        lun = options.luns
        while ',' in lun:
            id = lun[0:lun.find(',')]
            lun = lun[lun.find(',')+1:]
            luns.append(params.LogicalUnit(id=id))
        luns.append(params.LogicalUnit(id=lun))
        storage.set_logical_unit(luns)
        sd.set_storage(storage)
        newsd = self.api.storagedomains.add(sd)
        dc.storagedomains.add(newsd)

    def iso_domain(self, options):
        with open('/etc/ovirt-remote.conf', 'r') as f:
            line = f.readline()
            line = f.readline()
            options.address = line[line.find('=')+1:-1]
            line = f.readline()
            options.path = line[line.find('=')+1:-1]
        options.type = 'nfs'
        options._type = 'iso'
        options.domain = 'iso-domain'
        self.filedomain(options)

    def direct_lun(self, options):
        """ create a new dlun """

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

    def disk(self, options):
        """ create a new Vdisk """

        (sd, dc) = get_sd_dc_objects(self.api, options)
        dc = self.api.datacenters.get(id=dc.get_id())
        sd = dc.storagedomains.get(options.domain)
        size = int(options.size)*pow(1024, 3)
        disk = params.Disk(storage_domains=params.StorageDomains
                           (storage_domain=[sd]), size=size, type_='data',
                           interface=options.interface, format=options.format,
                           bootable=options.bootable, sparse=options.sparse,
                           name=options.disk)
        if sd.get_type() == 'volume':
            cinder = self.api.openstackvolumeproviders.get('cinder')
            vol_type = cinder.volumetypes.get('ceph')
            disk.set_openstack_volume_type(vol_type)
        self.api.disks.add(disk)
        sleep(5)

    def vm(self, options):
        """	Build a connection string from a dictionary of parameters.Returns
        string."""

        cluster = self.api.clusters.get(options.cluster)
        vm_name = options.vm
        network = params.Network(name=self.api.networks.list()[0].get_name())
        nic = params.NIC(name='eth0', network=network, interface='virtio')
        vm = params.VM(name=vm_name, cluster=cluster,
                       template=self.api.templates.get(name='Blank'))
        self.api.vms.add(vm)
        vm = self.api.vms.get(vm_name)
        vm.nics.add(nic)
        vm.update()
        return 0

    def vm_and_bootable_disk(self, options):
        self.vm(options)
        options.disk = options.vm + "_Disk_1"
        self.disk(options)
        sleep(5)
        sd = self.api.storagedomains.get(options.domain)
        vm = self.api.vms.get(options.vm)
        disk = sd.disks.get(options.disk)
        vm.disks.add(disk)
        sleep(2)
        disk = vm.disks.get(disk.get_name())
        disk.activate()

    def importfile(self, options):
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

    def filedomain(self, options):
        if '-1' not in options.host:
            host1 = self.api.hosts.get(options.host)
        else:
            (dc, host1) = self.get_host_and_dc(options)
        if options.type == 'nfs':
            _type = 'data'
        else:
            _type = 'iso'
        if options.address == '-1' and options.path == '-1':
            domain_dict = collect_params(options.domain)
            options.address = domain_dict['address']
            options.path = domain_dict['path']
        _storage = params.Storage
        storage = _storage(type_=options.type, address=options.address,
                           path=options.path)
        sd = params.StorageDomain(storage=storage, host=host1,
                                  name=options.domain, data_center=dc,
                                  type_=_type)
        newsd = self.api.storagedomains.add(sd)
        try:
            dc.storagedomains.add(newsd)
        except Exception, e:
            print e

    def openstack_volume_provider(self, options):
        """ add cinder domain """

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
