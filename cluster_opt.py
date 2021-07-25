import configparser

class Cluster(object):
    def __init__(self, in_cluster_name):
        self.cluster_name = in_cluster_name
        self.cluster_conf = None
        self.master_conf = None
        self.caves_conf = None
        self.cluster_token = None

    def scp_files(self):
        pass

    def edit_cluster_conf(self):
        pass

    def edit_mod_conf(self):
        # https://forums.kleientertainment.com/forums/topic/63723-guide-how-to-installconfigure-and-update-mods-on-dedicated-server/
        pass

    def edit_admin_list(self):
        # https://www.bilibili.com/video/BV1zy4y1g7S4
        pass



    def start_server(self):
        pass

    def stop_server(self):
        pass