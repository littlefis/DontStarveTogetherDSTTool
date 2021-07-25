import paramiko

class DSTServer(object):
    def __init__(self, in_ip, in_username, in_password, in_port):
        self.ip = in_ip
        self.username = in_username
        self.password = in_password
        self.port = in_port
        self.client = None

    def connect_to_client(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.client.connect(hostname=self.ip, port=self.port,
                             username=self.username, password=self.password)
            print('server connection successed')
            return True
        except paramiko.ssh_exception.AuthenticationException as e:
            print('server connection failed.')
            return False
        
    def install_dependencies(self):
        # https://forums.kleientertainment.com/forums/topic/64441-dedicated-server-quick-setup-guide-linux/
        stdin, stdout, stderr = self.client.exec_command('uname -m')
        if stdout.read().decode('utf-8').strip() == 'x86_64':
            install_cmd = 'sudo apt-get install libstdc++6:i386 libgcc1:i386 libcurl4-gnutls-dev:i386'
        else:
            install_cmd = 'sudo apt-get install libstdc++6 libgcc1 libcurl4-gnutls-dev'
        stdin, stdout, stderr = self.client.exec_command(install_cmd)
        if stdout.channel.recv_exit_status() == 0:
            print('dependencies installation successed.')
            return True
        else:
            print('dependencies installation failed.')
            return False

    def install_steamcmd(self):
        stdin, stdout, stderr = self.client.exec_command('sudo apt-get install steamcmd')
        if stdout.channel.recv_exit_status() == 0:
            print('steamcmd installation successed.')
            return True
        else:
            print('steamcmd installation failed.')
            return False
    