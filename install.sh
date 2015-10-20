#!/bin/bash

pythonRPM=`rpm -qa | grep ^python-2`
path=/usr/lib/${pythonRPM:0:6}${pythonRPM:7:3}/site-packages
etc_path=/etc/ovirt-remote/
is_sdk=`rpm -qa | grep "sdk-python"`
{ 
  if ! [ "$is_sdk" ]
  then
  yum install ovirt-engine-sdk-python -y 
  fi
  is_gcc=`rpm -qa | grep "^gcc"`
  if ! [ "$is_gcc" ]
  then
    yum install gcc -y 
  fi
  is_pydevel=`rpm -qa | grep "python-devel"`
  if ! [ "$is_pydevel" ]
  then
    yum install python-devel -y
  fi
  is_bpython=`rpm -qa | grep "bpython"`
  if ! [ "$is_bpython" ]
  then
    yum install bpython -y
  fi
  is_pip=`rpm -qa | grep "python-pip"`
  if ! [ "$is_pip" ]
  then
    yum install python-pip -y
  fi
  is_tabulate=`pip list | grep "tabulate"`
  if ! [ "$is_tabulate" ]
  then
    pip install tabulate 
  fi
  is_pexpect=`pip list | grep "pexpect"`
  if ! [ "$is_pexpect" ]
  then
    pip install pexpect 
  fi
  is_paramiko=`pip list | grep "paramiko"`
  if ! [ "$is_paramiko" ]
  then
    pip install paramiko
  fi
  is_configparser=`pip list | grep "configparser"`
  if ! [ "$is_configparser" ]
  then
    pip install configparser
  fi
  cp -rf ovirtremotesdk $path
  mkdir $etc_path 2>/dev/null 
  if ! [ -f /etc/ovirt-remote/domain.conf ]
  then
    cp domain.conf /etc/ovirt-remote/
  fi
  if ! [ -f /etc/ovirt-remote/hypervisors.conf ]
  then
    cp hypervisors.conf /etc/ovirt-remote/
  fi
  if ! [ -f /etc/ovirt-remote/ovirt-remote.conf ]
  then
    cp ovirt-remote.conf /etc/ovirt-remote/
  fi
  chmod +x scripts/ovirt-remote
  cp scripts/ovirt-remote /usr/bin/
  cp scripts/ovirt_watch_vm_up.py $etc_path
  if [ -d /usr/share/zsh/site-functions/ ]
  then
    cp completions/_ovirt_remote /usr/share/zsh/site-functions/
  fi
  cp completions/ovirt-remote /etc/bash_completion.d/
  cp completions/global_vars $etc_path
  echo "source /etc/bash_completion.d/ovirt-remote" >> ~/.bashrc
  source /etc/bash_completion.d/ovirt-remote
  if ! [ -d $etc_path ]
  then
    mkdir $etc_path
  fi
  cd dhcp_test
  make
  cd ..
  cp scripts/* $etc_path
  echo "installation successful"
} || {
       echo "oprtation failed"
     }
