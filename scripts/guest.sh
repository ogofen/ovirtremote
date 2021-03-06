#!/bin/bash
RE=`cat /etc/redhat-release`
if [ -z ${RE:40:1} ]
then
  yum install -y ovirt-guest-agent-common
  systemctl enable ovirt-guest-agent
  systemctl restart ovirt-guest-agent
  exit 0
fi
rpm -i ftp://rpmfind.net/linux/centos/7.1.1503/os/x86_64/Packages/qemu-guest-agent-2.1.0-4.el7.x86_64.rpm
rpm -i ftp://ftp.gwdg.de/linux/centos/6.6/updates/x86_64/Packages/qemu-guest-agent-0.12.1.2-2.448.el6_6.3.x86_64.rpm
rpm -i ftp://ftp.muug.mb.ca/mirror/fedora/epel/7/x86_64/o/ovirt-guest-agent-common-1.0.11-1.el7.noarch.rpm
rpm -i ftp://195.220.108.108/linux/epel/6/x86_64/ovirt-guest-agent-1.0.11-1.el6.noarch.rpm
systemctl enable ovirt-guest-agent
systemctl enable qemu-guest-agent
systemctl restart ovirt-guest-agent
systemctl restart qemu-guest-agent
service ovirt-guest-agent restart
exit 0
