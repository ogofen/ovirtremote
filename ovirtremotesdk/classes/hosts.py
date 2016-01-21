import paramiko
from time import sleep
import re
import sys


class Host(object):
    """ performs non py-sdk remote operations using paramiko """
    def __init__(self, address, passwd):
        self.address = address
        self.passwd = passwd

    def start_session(self, address, psswd):
        try:
            tmp_ssh = paramiko.SSHClient()
            tmp_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            tmp_ssh.connect(hostname=address,
                             username='root',
                             password=psswd, timeout=15)
        except Exception:
            print "Failed to open 'SSH session' to machine %s" % address
            tmp_ssh.close()
            sys.exit()
        return tmp_ssh

    def run_bash_command(self, bash_command):
        parm_host = self.start_session(self.address, self.passwd)
        stdin, stdout, stderr = parm_host.exec_command(bash_command)
        output = stdout.read()
        parm_host.close()
        return output

    def return_os(self):
        cmd = "cat /etc/redhat-release"
        str = self.run_bash_command(cmd)
        if "Fedora" in str:
            return "Fedora", re.findall(r'\d\.?\d', str)[0]
        else:
            return "Red Hat", re.findall(r'\d\.?\d', str)[0]

    def make_dir(self, path):
        cmd = "mkdir %s" % path
        try:
            self.run_bash_command(cmd)
        except Exception:
            return False
        return True

    def wget_file(self, dest, src):
        cmd = "wget -O %s %s --no-check-certificate" % (dest, src)
        try:
            self.run_bash_command(cmd)
        except Exception:
            return False
        return True

    def return_hostname(self):
        cmd = "dig -x %s" % (self.parameters['host_address'])
        try:
            str = self.run_bash_command(cmd)
        except Exception:
            return False
        return re.findall(r'R\t.+\.redhat\.com', str)[0][2:]

    def has_package(self, package):
        cmd = "rpm -qa | grep %s" % (package)
        if self.run_bash_command(cmd) is '':
            return False
        return True

    def set_hostname(self, hostname):
        cmd = "hostnamectl set-hostname %s" % (hostname)
        self.run_bash_command(cmd)

    def install_package(self, package):

        cmd = "yum install -y %s" % (package)
        self.run_bash_command(cmd)

    def has_file(self, path):
        parm_host = self.start_session(self.address, self.passwd)
        ftp = parm_host.open_sftp()
        try:
            ftp.lstat(path)
        except Exception:
            ftp.close()
            return False
        ftp.close()
        parm_host.close()
        return True

    def delete_file(self, path):
        parm_host = self.start_session(self.address, self.passwd)
        ftp = parm_host.open_sftp()
        ftp.remove(path)
        ftp.close()
        parm_host.close()

    def restart_services(self, service):
        cmd = "systemctl restart %s" % service
        self.run_bash_command(cmd)

    def fix_kickstart(self, dest):
        parm_host = self.start_session(self.address, self.passwd)
        ftp = parm_host.open_sftp()
        file = ftp.open(dest, 'r')
        filedata = file.read()
        fix = filedata.replace('reboot', 'shutdown')
        file.close()
        file = ftp.open(dest, 'w')
        file.write(fix)
        file.close()
        sleep(5)
        ftp.close()
        parm_host.close()

    def put_file(self, localpath, remotepath):
        parm_host = self.start_session(self.address, self.passwd)
        ftp = parm_host.open_sftp()
        ftp.put(localpath, remotepath)
        sleep(5)
        ftp.close()
        parm_host.close()
