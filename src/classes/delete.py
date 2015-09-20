from time import sleep
from ovirtremotesdk.utils import get_sd_dc_objects


class Delete(object):
    def __init__(self, ovirtremote):
        self.api = ovirtremote.api
        self.options = ovirtremote.options

    def __str__(self):
        return "delete"

    def get(self, string):
        if string == 'domain':
            return self.domain
        if string == 'vm':
            return self.vm
        if string == 'host':
            return self.host
        if string == 'all_vms_and_disks':
            return self.all_vms_and_disks
        if string == 'cluster':
            return self.cluster

    def domain(self):
        """ removes a domain """

        options = self.options
        (sd, dc) = get_sd_dc_objects(self.api, options)
        if sd is None:
            print "storage domain wasn't found"
            return 1
        if sd.get_status().get_state() == 'active':
            try:
                sd.deactivate()
            except Exception, e:
                print e
                return 1
        if dc is not None:
            sd_no_dc = self.api.storagedomains.get(options.domain)
            while sd.get_status().get_state() != 'maintenance':
                sleep(2)
                sd = dc.storagedomains.get(options.domain)
            sd.delete()
            sleep(10)
        for host in self.api.hosts.list():
            if dc.clusters.get(id=host.get_cluster().get_id()) is not None:
                sd_no_dc.set_host(host)
        if sd.get_type() == 'iso':
            sd_no_dc.delete(sd_no_dc)
            return 0

        sd_no_dc.set_format('True')
        sd_no_dc.delete(sd_no_dc)
        return 0

    def all_vms_and_disks(self):
        for vm in self.api.vms.list():
            try:
                vm.stop()
            except Exception:
                pass
            sleep(5)
            vm.delete()
        for disk in self.api.disks.list():
            if disk.get_name() == 'OVF_STORE':
                continue
            if disk.get_status().get_state() != 'locked':
                try:
                    disk.delete()
                except Exception:
                    pass

    def vm(self):
        """ removes a vm """

        options = self.options
        vm = self.api.vms.get(options.vm)
        if vm.get_status().get_state() != 'down':
            try:
                vm.stop()
                sleep(8)
            except Exception:
                pass
        vm.delete()

    def host(self):
        """ removes a host """

        options = self.options
        host = self.api.hosts.get(options.host)
        try:
            host.deactivate()
        except Exception:
            pass
        sleep(3)
        host.delete()

    def cluster(self):
        """ removes a cluster """

        options = self.options
        cl = self.api.clusters.get(options.cluster)
        cl.delete()

    def disk(self):
        """ removes a domain """

        options = self.options
        disk = self.api.disks.get(options.disk)
        disk.delete()
