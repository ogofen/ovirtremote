import paramiko
from time import sleep
import re


class Host(object):
    def __init__(self, address, psswd):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(hostname=address,
                         username='root',
                         password=psswd, timeout=10)

    def __del__(self):
        self.ssh.close()

    def run_bash_command(self, bash_command):
        stdin, stdout, stderr = self.ssh.exec_command(bash_command)
        output = stdout.read()
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
        ftp = self.ssh.open_sftp()
        try:
            ftp.lstat(path)
        except Exception:
            ftp.close()
            return False
        ftp.close()
        return True

    def delete_file(self, path):
        ftp = self.ssh.open_sftp()
        ftp.remove(path)
        ftp.close()

    def restart_services(self, service):
        cmd = "systemctl restart %s" % service
        self.run_bash_command(cmd)

    def fix_kickstart(self, dest):
        ftp = self.ssh.open_sftp()
        file = ftp.open(dest, 'r')
        filedata = file.read()
        fix = filedata.replace('reboot', 'shutdown')
        file.close()
        file = ftp.open(dest, 'w')
        file.write(fix)
        file.close()
        sleep(5)
        ftp.close()

    def put_file(self, localpath, remotepath):
        ftp = self.ssh.open_sftp()
        ftp.put(localpath, remotepath)
        sleep(5)
        ftp.close()
