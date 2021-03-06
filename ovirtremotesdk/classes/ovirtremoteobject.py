#!/usr/bin/python
from ovirtsdk.api import API
from hosts import Host
from configparser import SafeConfigParser
import sys


class ovirt_remote_base(object):
    """basic ovirt-remote class that contains the common defs"""
    def __init__(self):
        self.image_path = '/.iso'
        self.path = "/etc/ovirt-remote"

    def write_object_to_file(self, path, obj):
        """ writing an object to file for further bash_completion use"""
        file = open("/tmp/"+path, 'w')
        file.write(obj)

    def collect_params(self, setup, confile):
        parser = SafeConfigParser()
        parser.read('/etc/ovirt-remote/%s.conf' % confile)
        s = dict()
        try:
            s['url'] = parser.get(setup, 'url').encode('ascii')
        except Exception:
            pass
        try:
            s['cluster'] = parser.get(setup, 'cluster').encode('ascii')
        except Exception:
            pass
        try:
            s['name'] = parser.get(setup, 'name').encode('ascii')
        except Exception:
            pass
        try:
            s['user'] = parser.get(setup, 'user').encode('ascii')
        except Exception:
            pass
        try:
            s['password'] = parser.get(setup, 'password').encode('ascii')
        except Exception:
            pass
        try:
            s['secret_value'] = parser.get(setup,
                                           'secret_value').encode('ascii')
        except Exception:
            pass
        try:
            s['uuid'] = parser.get(setup, 'uuid').encode('ascii')
        except Exception:
            pass
        try:
            s['tenant'] = parser.get(setup, 'tenant').encode('ascii')
        except Exception:
            pass
        try:
            s['auth_url'] = parser.get(setup, 'auth_url').encode('ascii')
        except Exception:
            pass
        try:
            s['password'] = parser.get(setup, 'password').encode('ascii')
        except Exception:
            pass
        try:
            s['address'] = parser.get(setup, 'address').encode('ascii')
        except Exception:
            pass
        try:
            s['path'] = parser.get(setup, 'path').encode('ascii')
        except Exception:
            pass
        try:
            s['luns'] = parser.get(setup, 'luns').encode('ascii')
        except Exception:
            pass
        try:
            s['ks'] = parser.get(setup, 'ks').encode('ascii')
        except Exception:
            pass
        try:
            s['initrd'] = parser.get(setup, 'initrd').encode('ascii')
        except Exception:
            pass
        try:
            s['kernel'] = parser.get(setup, 'kernel').encode('ascii')
        except Exception:
            pass
        return s


class remote_operation_object(ovirt_remote_base):
    """simple remote operation class that connects to an oVirt setup and can perform simple fuctions"""
    def __init__(self, setup, machine_readable):
        super(remote_operation_object, self).__init__()
        self.machine_readable = machine_readable
        self.setup = self.collect_params(setup, "ovirt-remote")
        try:
            self.api = API(url=self.setup['url'],
                           password=self.setup['password'],
                           username=self.setup['user'], insecure=True)
        except Exception:
            print "ovirt-remote failed to connect to engine"
            sys.exit(1)

    def get_sd_dc_objects(self, domain):
        sd = self.api.storagedomains.get(domain)
        try:
            dc = sd.get_data_centers().get_data_center()[0]
        except Exception:
            return sd, None
        dc = self.api.datacenters.get(id=dc.get_id())
        sd = dc.storagedomains.get(domain)
        return sd, dc

    def vm_ip(self, vmname, hostname):
        vm = self.api.vms.get(vmname)
        host = self.api.hosts.get(hostname)
        mac = vm.nics.list()[0].get_mac().get_address()
        bridge = self.api.networks.list()[0].get_name()
        password = self.collect_params(host.get_name(), 'hypervisors')['password']
        try:
            r_host = Host(host.get_address(), password)
        except Exception, e:
            return e
        cmd = '/give_mac_return_ip -m %s -i %s' % (mac, bridge)
        out = r_host.run_bash_command(cmd)
        return out[out.find('Acquired IP:')+13:].rstrip()

    def select_host_from_cluster(self, cluster):
        for host in self.api.hosts.list():
            if host.get_cluster().get_id() == cluster:
                password = self.collect_params(host.get_name(),
                                               'hypervisors')['password']
                r_host = Host(host.get_address(), password)
                if not r_host.has_file('/give_mac_return_ip'):
                    self.ini_host(host)
                return host


