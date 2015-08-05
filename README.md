ovirt-remote:a command line tool for remote engines
----------------------------------------------------------
ovirtremote provides a command line api that allows sysadmins or qe to perform multiple operations from a private desktop to
one or more remote ovirt-engines.
the api collection supports four methods:
[get](#get), [delete](#delete), [new](#new) and [set](#set).
setup configuration and other settings should be edited at the ovirt-remote.conf file.

ovirt-remote functionallity:
(1) Querying inforamtion about a certain setup
(2) Perfoming domain and Vm creation
(3) Performing domain and Vm deletion
(4) Modifing oVirt entities with set command


- ###get
  example 1: get's lun's information.  
  - ovirt-remote [setup] get available_luns_info --host [string]  
  NOTE:if --host is not mentioned,ovirt-remote will pick one from hosts list  
  
  example 2: returns all domains info  
  - ovirt-remote get [setup] domains_info

- ###delete
  example 1:deletes a domain.  
  - ovirt-remote [setup] delete domain --domainname [string] --datacenter [string]  
  NOTE:if --datacenter is not mentioned, ovirt-remote will pick the 'Default' datacenter  

- ###new
  example 1:new block domain.  
  - ovirt-remote [setup] new block-domain --datacenter [string] --domain [string] --luns [number] --type [fcp,iscsi] --setup [number]

  example 2:new iso domain.  
  - ovirt-remote [setup] new iso-domain --datacenter [string]

- ###set
  example 1:set guest-agent to vm.  
  - ovirt-remote [setup] set guestagent --vm_address [string] --password [string]  


How to install:
--------------
- git clone https://github.com/ogofen/ovirtremote.git
- cd ovirtremote
- sudo ./install.sh

dependancies:
- ovirt-engine-sdk
- python-devel
- python-pip
- tabulate(py module)
- paramiko
- configparser
- optparser

please submit issues(bugs) here and RFE's at -> https://mojo.redhat.com/docs/DOC-1040466
---------------
for more info -> https://www.youtube.com/watch?v=G2sK6lNq-4Q
--------------
