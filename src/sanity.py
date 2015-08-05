#!/usr/bin/python
from termcolor import colored
from utils import pull_sanity_options
from optparse import OptionParser
import sys
from time import sleep
from classes._ovirtremote import ovirtremote
from random import randint
import os
import pudb
# pudb.set_trace()


def has_ovf(disks_list):
    for disk in disks_list:
        if disk.get_name() == "OVF_STORE":
            return True
    return False


class sanity(object):
    """ This Function connects To our engine,classes and db
    """

    def __init__(self, conf):
        self.options = pull_sanity_options(conf)
        self.formats = ['raw', 'cow']
        self.interfaces = ['virtio', 'virtio_scsi', 'ide']
        self.stories = ['Domains creation', 'Disk creation',
                        'Disks verification', 'Random disk creation test',
                        'Live virtual disks attach and edit', 'VMs launch']
        self.domains = ['iscsi-domain', 'fcp-domain', 'cinder']
        # self.domains = ['nfs-domain', 'iscsi-domain', 'cinder']
        # self.domains = ['cinder']

    def Main_Test(self, o_remote, parser):
        print "Storage Sanity Test Started"
        print "---------------------------"
        sleep(3)
        if parser.domain != 'no':
            print "- Story I: Domains creation"
            sleep(3)
            self.exec_story(self.domains_creation, o_remote, self.stories[0])
            print ""
        if parser.disk != 'no':
            print "- Story II: Disks creation"
            sleep(3)
            self.exec_story(self.disks_creation, o_remote, self.stories[1])
            print ""
            print "- Story III: Disks verification"
            self.exec_story(self.disks_verifaction, o_remote, self.stories[2])
            self.clean_disks(o_remote)
        if parser.vms != 'no':
            print ""
            print "- Story IV: Random disks creation test"
            self.exec_story(self.create_random_disk, o_remote, self.stories[3])
            print ""
            print "- Story V: Live virtual disks test"
            self.exec_story(self.vms_storage_growth, o_remote, self.stories[4])
            print ""
            print "- Story VI: VM's launch and live storage growth"
            self.exec_story(self.vms_launch, o_remote, self.stories[5])

    def exec_story(self, func, o_remote, story):
        for domain_name in self.domains:
            index = self.domains.index(domain_name)
            print "      Case %s: %s, %s " % (index + 1, story, domain_name),
            sys.stdout.flush()
            func(o_remote, self.options[domain_name])

    def vms_storage_growth(self, o_remote, options):
            o_remote.new.vm(options)
            vm = o_remote.api.vms.get(options.vm)
            while True:
                try:
                    o_remote.set.attach_disk(options)
                except Exception:
                    sleep(1)
                    continue
                else:
                    sleep(3)
                    hd = vm.disks.get('disk')
                    hd.set_alias('disk_' + options.domain)
                    hd.update()
                    hd.set_provisioned_size(8*pow(1024, 3))
                    hd.update()
                    hd = vm.disks.list()[0]
                    while hd.get_status().get_state() == 'locked':
                        sleep(5)
                        hd = vm.disks.list()[0]
                    break
            print colored("     Pass", 'green')

    def vms_launch(self, o_remote, options):
        cmd = "ovirt-remote set operating_system --vmname %s --setup %s"\
            % (options.vm, options.setup)
        sleep(5)
        os.system(cmd)
        print colored("     Pass", 'green')
        return True

    def domains_creation(self, o_remote, options):
        domain_name = options.domain
        if domain_name == 'nfs-domain':
            try:
                o_remote.new.filedomain(options)
            except Exception:
                print colored("     Failure", 'red')
                return False
        elif domain_name == 'cinder':
            try:
                o_remote.new.openstack_volume_provider(options)
            except Exception:
                print colored("  Failure", 'red')
                return False
        elif domain_name == 'iso-domain':
            try:
                o_remote.new.iso_domain(options)
            except Exception:
                print colored("  Failure", 'red')
                return False
        else:
            try:
                o_remote.new.blockdomain(options)
            except Exception:
                print colored("     Pass", 'green')
        sleep(5)
        print colored("  Pass", 'green')

    def disks_verifaction(self, o_remote, options):
        sd = o_remote.api.storagedomains.get(options.domain)
        disks = sd.disks
        if sd.get_name() == 'cinder':
            if len(disks.list()) != 6:
                print colored("   Failure", 'red')
                return False
        elif sd.get_name() == 'fcp-domain' or sd.get_name() == 'iscsi-domain':
            if has_ovf(disks.list()):
                if len(disks.list()) != 8:
                    print colored("   Failure", 'red')
                    return False
            else:
                if len(disks.list()) != 6:
                    print colored("   Failure", 'red')
                    return False
        elif sd.get_name() == 'nfs-domain':
                if has_ovf(disks.list()):
                    if len(disks.list()) != 11:
                        print colored("   Failure", 'red')
                        return False
                else:
                    if len(disks.list()) != 9:
                        print colored("   Failure", 'red')
                        return False
        print colored("  Pass", 'green')
        return self.clean_disks(o_remote)

    def clean_disks(self, o_remote):
        for disk in o_remote.api.disks.list():
            if disk.get_name() != 'OVF_STORE':
                disk.delete()
                sleep(3)
        return True

    def create_random_disk(self, o_remote, options):
        while True:
            options.format = self.formats[randint(0, 1)]
            options.sparse = randint(0, 1)
            options.interface = self.interfaces[randint(0, 2)]
            options.size = 2
            options.bootable = True
            try:
                o_remote.new.disk(options)
            except Exception:
                pass
            else:
                print colored("  Pass", 'green')
                return True
        return True

    def disks_creation(self, o_remote, options):
        options.size = '1'
        domain = options.domain
        if domain == 'fcp-domain' or domain == 'iscsi-domain':
            block_flag = True
        else:
            block_flag = False
        for format in self.formats:
            options.format = format
            for interface in self.interfaces:
                options.interface = interface
                if options.domain == 'cinder' and format == 'cow':
                    try:
                        options.sparse = False
                        o_remote.new.disk(options)
                    except Exception:
                        try:
                            options.sparse = True
                            o_remote.new.disk(options)
                        except Exception:
                            block_flag = True
                        else:
                            print colored("   Failure", 'red')
                            return False
                    else:
                        print colored("   Failure", 'red')
                        return False
                elif format == 'cow':
                    try:
                        options.sparse = False
                        o_remote.new.disk(options)
                    except Exception:
                        options.sparse = True
                        o_remote.new.disk(options)
                    else:
                        print colored("   Failure", 'red')
                        return False
                if format == 'raw' and block_flag is True:
                    try:
                        options.sparse = True
                        o_remote.new.disk(options)
                    except Exception:
                        options.sparse = False
                        o_remote.new.disk(options)
                    else:
                        print colored("   Failure", 'red')
                        return False
                elif format == 'raw':
                    options.sparse = True
                    o_remote.new.disk(options)
                    options.sparse = False
                    o_remote.new.disk(options)
        print colored("  Pass", 'green')
        return True


if __name__ == "__main__":
    parser = OptionParser(usage='%prog [options] "name"', version='1.22',)
    parser.add_option("--domain", dest="domain", default='yes')
    parser.add_option("--disk", dest="disk", default='yes')
    parser.add_option("--setup", dest="url", default='0')
    parser.add_option("--vms", dest="vms", default='0')
    (par, args) = parser.parse_args(sys.argv)
    print ''
    ovirtremote = ovirtremote(sys.argv)
#    Sanity = sanity('./sanity-0.conf')
    Sanity = sanity('./sanity.conf')
    sys.exit(Sanity.Main_Test(ovirtremote, par))
