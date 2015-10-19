#!/bin/bash
RE=`cat /etc/redhat-release`
if [ -z ${RE:40:1} ]
then
  yum install -y ovirt-guest-agent-common
  systemctl enable ovirt-guest-agent
  systemctl restart ovirt-guest-agent
  exit 0
fi
yum-config-manager --add-repo=http://mirror.utexas.edu/epel/${RE:40:1}/x86_64/
yum-config-manager --add-repo=http://download.eng.tlv.redhat.com/pub/rhel/released/RHEL-${RE:40:1}/${RE:40:1}.${RE:42:1}/Server/x86_64/os/
rpm --import http://mirror.utexas.edu/epel/RPM-GPG-KEY-EPEL-${RE:40:1}
rpm --import http://download.eng.tlv.redhat.com/pub/rhel/released/RHEL-${RE:40:1}/${RE:40:1}.${RE:42:1}/Server/x86_64/os/RPM-GPG-KEY-redhat-release
yum install -y ovirt-guest-agent
systemctl enable ovirt-guest-agent
systemctl restart ovirt-guest-agent
service ovirt-guest-agent restart
exit 0
