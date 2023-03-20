from shutil import which
from subprocess import STDOUT, check_call
import os

CNF_SERVER = '\n$ModLoad imudp\n$UDPServerRun {0}\n'
CNF_SERVER_TEMPLATE = '\n### ADDED ###\n$template remote-incoming-logs,"/var/log/%HOSTNAME%/%PROGRAMNAME%.log"\n*.* ?remote-incoming-logs\n& ~'

CNF_CLIENT = '\n### ADDED ###\n*.* @{0}:{1}\n'
CNF_CLIENT_DWN = '\n$ActionQueueFileName queue\n$ActionQueueMaxDiskSpace 1g\n$ActionQueueSaveOnShutdown on\n$ActionQueueType LinkedList\n$ActionResumeRetryCount -1'

CNF_PATH = '/etc/rsyslog.conf'
CMD_TEST_CNF = 'rsyslogd -f /etc/rsyslog.conf -'


def is_tool(name):
    return which(name) is not None


def update_apt():
    print('[DEP]Updating apt...')
    check_call(['sudo', 'apt-get', 'update', '--fix-missing'],
               stdout=open(os.devnull, 'wb'), stderr=STDOUT)


def install_rsyslog():
    if not is_tool('rsyslogd'):
        update_apt()
        print('[DEP]Installing rsyslog...')
        check_call(['sudo', 'apt-get', 'install', '-y', 'rsyslog'],
                   stdout=open(os.devnull, 'wb'), stderr=STDOUT)
        check_call(['sudo', 'systemctl', 'start', 'rsyslog'],
                   stdout=open(os.devnull, 'wb'), stderr=STDOUT)
        check_call(['sudo', 'systemctl', 'enable', 'rsyslog'],
                   stdout=open(os.devnull, 'wb'), stderr=STDOUT)
    else:
        print('[DEP]Up to date!')


def set_hostname(hostname):
    print('[MISC]Changing hostname...')
    check_call(['sudo', 'hostnamectl', 'set-hostname', hostname],
               stdout=open(os.devnull, 'wb'), stderr=STDOUT)

    updated_content = []
    with open('/etc/hosts', 'r') as f:
        content = f.read().split('\n')
        for line in content:
            if '127.0.1.1' not in line:
                updated_content.append(f'{line}\n')
            else:
                updated_content.append(f'127.0.1.1\t{hostname}\n')

    with open('/etc/hosts', 'w') as f:
        f.writelines(updated_content)


def configure_client(hostname, server_ip, server_port):
    set_hostname(hostname)
    with open(CNF_PATH, 'a') as f:
        print('[CNF]Writing configuration...')
        config = [CNF_CLIENT.format(server_ip, server_port), CNF_CLIENT_DWN]
        f.writelines(config)


def configure_server(hostname, port):
    set_hostname(hostname)
    with open(CNF_PATH, 'a') as f:
        print('[CNF]Writing configuration...')
        config = [CNF_SERVER.format(port), CNF_SERVER_TEMPLATE]
        f.writelines(config)


def test_configuration():
    print('[CNF]Checking rsyslog configuration...')
    check_call(['sudo', 'rsyslogd', '-f', CNF_PATH, '-N1'],
               stdout=open(os.devnull, 'wb'), stderr=STDOUT)
    check_call(['sudo', 'systemctl', 'restart', 'rsyslog'],
               stdout=open(os.devnull, 'wb'), stderr=STDOUT)
    print('[CNF]Everything is good!')


def setup():
    install_rsyslog()

    choice = None
    while choice not in ['S', 'C', '']:
        choice = input('Server(S) | Client(C) or ENTER to quit: ').upper()

    if choice == '':
        return 0

    hostname = input('Hostname: ')

    if choice == 'C':
        print("\n==Client Configuration==")
        server_ip = input('ServerIp: ')
        server_port = input('ServerPort: ')
        configure_client(hostname, server_ip, server_port)

    if choice == 'S':
        print("\n==Server Configuration==")
        server_port = input('ServerPort: ')
        configure_server(hostname, server_port)

    test_configuration()


setup()
