import os
import shutil
import paramiko

class DSTServer(object):
    def __init__(self, in_ip, in_username, in_password, in_port):
        self.ip = in_ip
        self.username = in_username
        self.password = in_password
        self.port = in_port
        self.client = None
        self.clusters = set()
        self.running_clusters = dict()

    def connect_to_server(self):
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

    def install_dst(self):
        stdin, stdout, stderr = self.client.exec_command('steamcmd +force_install_dir /home/{}/dst +login anonymous +app_update 343050 validate +quit'.format(self.username))
        
        while not stdout.channel.exit_status_ready():
            print(stdout.readline())
            if stdout.channel.exit_status_ready():
                print(stdout.readlines())

        if stdout.channel.recv_exit_status() == 0:
            print('dst installation successed.')
            return True
        else:
            print('dst installation failed.')
            return False
    
    def upload_cluster(self, local_path, server_cluster_name):
        if os.path.isdir(local_path):
            zip_file_path = shutil.make_archive(server_cluster_name, 'zip', local_path)
            server_zip_dir = '/home/{}/.klei/DoNotStarveTogether/{}/'.format(self.username, server_cluster_name)
            server_zip_path = server_zip_dir + '{}.zip'.format(server_cluster_name)
        else:
            zip_file_path = local_path
            server_zip_dir = '/home/{}/.klei/DoNotStarveTogether/'.format(self.username)
            server_zip_path = server_zip_dir + '{}.zip'.format(server_cluster_name)
        
        sftp_client = self.client.open_sftp()
        server_extracted_path = '/home/{}/.klei/DoNotStarveTogether/{}/'.format(self.username, server_cluster_name)
        if self.is_file_exist(server_extracted_path):
            print(server_extracted_path, 'exists')
            self.client.exec_command('rm -r {}'.format(server_extracted_path))

        stdin, stdout, stderr = self.client.exec_command('mkdir -p {}'.format(server_zip_dir))
        if stdout.channel.recv_exit_status() != 0:
            print('mkdir failed')
            return False
        
        sftp_client.put(zip_file_path, server_zip_path)
        if not self.is_file_exist(server_zip_path):
            print('scp failed')
            return False
        
        stdin, stdout, stderr = self.client.exec_command('unzip {} -d {}'.format(server_zip_path, server_zip_dir))
        if stdout.channel.recv_exit_status() != 0:
            print('server unzip failed')
            return False
        stdin, stdout, stderr = self.client.exec_command('rm {}'.format(server_zip_path))
        os.remove(zip_file_path)
        self.clusters.add(server_cluster_name)
        return True

    def download_cluster(self, local_path, server_cluster_name):
        server_cluster_path = '/home/{}/.klei/DoNotStarveTogether/{}'.format(self.username, server_cluster_name)
        if not self.is_file_exist(server_cluster_path):
            print(server_cluster_name, 'not exist on server')
            return False
        server_zip_path = server_cluster_path + '.zip'
        
        sftp_client = self.client.open_sftp()
        if self.is_file_exist(server_zip_path):
            print('zip file exist',)
            sftp_client.remove(server_zip_path)

        stdin, stdout, stderr = self.client.exec_command(
            'cd /home/{}/.klei/DoNotStarveTogether/;zip -r -q {}.zip {}'.format(
                self.username, server_cluster_name, server_cluster_name))
        while not stdout.channel.exit_status_ready():
            continue
        
        if not self.is_file_exist(server_zip_path):
            print('server zip file not exist')
            return False
        local_file_path = local_path + '/' + server_cluster_name + '.zip'
        sftp_client.get(server_zip_path, local_file_path)
        if not os.path.exists(local_file_path):
            print('download failed')
            return False
        # sftp_client.remove(server_zip_path)
        return True

    def load_server_clusters(self, server_cluster_name):
        # check file for not running
        # check pid by name for running
        pass

    def start_cluster(self, server_cluster_name):
        base_cmd = 'cd /home/{}/dst/bin; ./dontstarve_dedicated_server_nullrenderer -console -cluster {}'.format(self.username, server_cluster_name)
        master_cmd = base_cmd + ' -shard Master'
        caves_cmd = base_cmd + ' -shard Caves'
        stdin, stdout, stderr = self.client.exec_command(master_cmd)
        while not stdout.channel.exit_status_ready():
            line = stdout.readline()
            if 'Your Server Will Not Start' in line:
                print('server start completed')
                break
            print(line)
            if stdout.channel.exit_status_ready():
                print(stdout.readlines())
        stdin, stdout, stderr = self.client.exec_command(caves_cmd)
        while not stdout.channel.exit_status_ready():
            line = stdout.readline()
            if 'Your Server Will Not Start' in line:
                print('server start completed')
                break
            print(line)
            if stdout.channel.exit_status_ready():
                print(stdout.readlines())
        
        stdin, stdout, stderr = self.client.exec_command('ps -ef | grep \'[c]luster {}\' | awk \'{{print $2}}\''.format(server_cluster_name))
        pids = [line.strip() for line in stdout.readlines()]
        self.running_clusters[server_cluster_name] = pids
        print('server start with pids ', pids)

    def stop_cluster(self, server_cluster_name):
        for pid in self.running_clusters.pop(server_cluster_name, list()):
            stdin, stdout, stderr = self.client.exec_command('kill {}'.format(pid))
        
    def is_file_exist(self, path):
        stdin, stdout, stderr = self.client.exec_command('ls {}'.format(path))
        return stdout.channel.recv_exit_status() == 0