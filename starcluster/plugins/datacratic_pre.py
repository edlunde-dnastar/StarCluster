import datetime
from starcluster import clustersetup
from starcluster.logger import log
from starcluster import utils


class DatacraticPrePlugin(clustersetup.DefaultClusterSetup):

    def __init__(self, tag_billcode, mount):
        self.tag_billcode = tag_billcode
        self.mount = mount

    def run(self, nodes, master, user, user_shell, volumes):
        master.add_tag("billcode", self.tag_billcode)

    def on_add_node(self, node, nodes, master, user, user_shell, volumes):

        node.add_tag("billcode", self.tag_billcode)
        #create a 20GB swap in a background process
        launch_time = utils.iso_to_datetime_tuple(node.launch_time)
        shutdown_in = int((launch_time + datetime.timedelta(minutes=235) -
                          utils.get_utc_now()).total_seconds() / 60)
        if shutdown_in > 0:
            log.info("Shutdown order in 3h55 minutes from launch ("
                     + str(shutdown_in) + ")")
            node.ssh.execute_async("shutdown -h +" + str(shutdown_in) +
                                   " StarCluster datacratic plugin "
                                   "sets node auto shutdown in 3h55 minutes.")
        else:
            log.error("Shutdown is already expired. "
                      "Granting the current hour block.")
            shutdown_in = 60 - shutdown_in % 60 + 1
            node.ssh.execute_async("shutdown -h +" + str(shutdown_in) +
                                   " StarCluster datacratic plugin "
                                   "sets node auto shutdown in current "
                                   "hour block")
        log.info("Creating 20GB swap space on node " + node.alias)
        msg = node.ssh.execute("file /mnt/20GB.swap", ignore_exit_status=True)
        if msg[0].find("ERROR") != -1:
            node.ssh.execute_async(
                'echo "(/bin/dd if=/dev/zero of=/mnt/20GB.swap bs=1M '
                'count=20480; '
                '/sbin/mkswap /mnt/20GB.swap; '
                '/sbin/swapon /mnt/20GB.swap;) &" > createSwap.sh; '
                'bash createSwap.sh; rm createSwap.sh')

        if False:
            if node.ssh.execute("mount | grep sge6 | wc -l")[0] == "0":
                log.info("Mounting /opt/sge6 from master")
                node.ssh.execute("rm -rf /opt/sge6; "
                                "mkdir /opt/sge6")
                node.ssh.execute("sshfs -o allow_other -C -o workaround=all "
                                "-o reconnect -o sshfs_sync "
                                "master:/opt/sge6 /opt/sge6")
            else:
                log.error("/opt/sge6 is already mounted")

            res = node.ssh.execute("mount | grep " + self.mount + " | wc -l")[0]
            if res[0] == "0":
                log.info("Mounting " + self.mount + " from master")
                node.ssh.execute("rm -rf /root/" + self.mount + " && "
                                 "mkdir /root/" + self.mount + " && "
                                 "sshfs -o allow_other -C -o workaround=all "
                                 "-o reconnect -o sshfs_sync "
                                 "master:" + self.mount + " " + self.mount)
            else:
                log.error("/root/" + self.mount + " is already mounted")

        if True:
                node.ssh.execute("scp master:/home/useradd.sh /home/.")
        else:
            if node.ssh.execute("mount | grep home | wc -l")[0] == "0":
                log.info("Mounting /home from master")
                node.ssh.execute("sshfs -o allow_other -C -o workaround=all "
                                 "-o reconnect -o sshfs_sync -o nonempty "
                                 "master:/home /home")
            else:
                log.error("/home is already mounted")

        # Run the /home/useradd.sh script if it exists
        # that script is generated by saltstack and contains
        # the commands used to setup users on the worker nodes
        node.ssh.execute("test -f /home/useradd.sh && /home/useradd.sh")

        log.info("Creating /mnt/s3cache")
        msg = node.ssh.execute("file /mnt/s3cache", ignore_exit_status=True)
        if msg[0].find("ERROR") == -1:
                log.warning("/mnt/s3Cache already exists")
        else:
                node.ssh.execute("install -d -m 1777 /mnt/s3cache")

    def on_remove_node(self, node, nodes, master, user, user_shell, volumes):
        pass

    def clean_cluster(self, nodes, master, user, user_shell, volumes):
        pass

    def recover(self, nodes, master, user, user_shell, volumes):
        pass
