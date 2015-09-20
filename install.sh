#!/bin/bash

pythonRPM=`rpm -qa | grep ^python-2`
path=/usr/lib/${pythonRPM:0:6}${pythonRPM:7:3}/site-packages
sudo_user_path=/home/$SUDO_USER
if [ -z $SUDO_USER ]
then
  SUDO_USER=root
  sudo_user_path=/$SUDO_USER
fi
is_sdk=`rpm -qa | grep "sdk-python"`
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

if ! [ -d $path/ovirtremotesdk ]
then
  mkdir $path/ovirtremotesdk
fi
cp -r src/* $path/ovirtremotesdk/
if ! [ -f /etc/ovirt-remote.conf ]
then
  cp ovirt-remote.conf /etc/
fi
chmod +x bin/ovirt-remote

cp bin/ovirt-remote /usr/bin/
if [ -d /usr/share/zsh/site-functions/ ]
then
  cp completions/_ovirt_remote /usr/share/zsh/site-functions/
fi
cp completions/ovirt-remote /etc/bash_completion.d/
cp completions/global_vars $sudo_user_path
echo "source /etc/bash_completion.d/ovirt-remote" >> ~/.bashrc
source /etc/bash_completion.d/ovirt-remote
if ! [ -d $sudo_user_path/.ovirt-remote ]
then
  mkdir $sudo_user_path/.ovirt-remote
  chown -R $SUDO_USER:$SUDO_USER $sudo_user_path/.ovirt-remote 
fi
cd dhcp_test
make
cd ..
cp bin/* $sudo_user_path/.ovirt-remote/
echo "installation successful"
