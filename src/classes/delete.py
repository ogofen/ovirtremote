from time import sleep
from ovirtremotesdk.utils import get_sd_dc_objects


class Delete(object):
    def __init__(self, ovirtremote):
        self.api = ovirtremote.api

    def __str__(self):
        return "delete"

    def exec_cmd(self, string, options):
        if string == 'domain':
            return self.domain(options.domain)
        elif string == 'vm':
            return self.vm(options.vm)
        elif string == 'host':
            return self.host(options.host)
        elif string == 'all_vms_and_disks':
            return self.all_vms_and_disks()
        elif string == 'cluster':
            return self.cluster(options.cluster)

    def domain(self, domain_name):
        """ removes a domain """

        (sd, dc) = get_sd_dc_objects(self.api, domain_name)
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
            sd_no_dc = self.api.storagedomains.get(domain_name)
            while sd.get_status().get_state() != 'maintenance':
                sleep(2)
                sd = dc.storagedomains.get(domain_name)
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

    def vm(self, vm_name):
        """ removes a vm """

        vm = self.api.vms.get(vm_name)
        if vm.get_status().get_state() != 'down':
            try:
                vm.stop()
                sleep(8)
            except Exception:
                pass
        vm.delete()

    def host(self, host_name):
        """ removes a host """

        host = self.api.hosts.get(host_name)
        try:
            host.deactivate()
        except Exception:
            pass
        sleep(3)
        host.delete()

    def cluster(self, cluster):
        """ removes a cluster """

        cl = self.api.clusters.get(cluster)
        cl.delete()

    def disk(self, disk_name):
        """ removes a domain """

        disk = self.api.disks.get(disk_name)
        disk.delete()
