"""
WIREGEN
"""

from csv import reader
from io import StringIO
from os import path, makedirs

from ipaddress import IPv4Address as IPv4, IPv4Network

from wiregen.classes import ConfigFile, Interface, Peer
from wiregen.common import generate_preshared_key


def ingest_client_csv(server: Interface, file_path: str, mikrotik: bool = False) -> None:
    """"""

    with open(file_path, 'r') as file:
        clients_file = StringIO(file.read())

    client_csv = reader(clients_file)

    header = next(clients_file).split(',')
    invert_header = {item: i for i, item in enumerate(header)}

    client_configs: dict[str, ConfigFile] = {}
    server_peers: list[Peer] = []

    server_endpoint = f'{server.Endpoint}:{server.ListenPort}'

    # Create the WG address pool and remove the server from available hosts
    address_pool = list(IPv4Network(server.Address, strict=False).hosts())
    address_pool.remove(IPv4(server.Address.split('/')[0]))

    # a script designed to be pasted into a Mirkotik CLI
    if mikrotik:
        mikrotik_script = server.mikrotik()

    for client_data in client_csv:
        get_info = lambda x: client_data[invert_header[x]]

        psk = generate_preshared_key()

        # wg_address = get_info('Interface Address')
        wg_address = str(address_pool.pop(0))
        hostname = get_info('Hostname')

        client = Interface(wg_address, hostname=hostname, interface_name=get_info('Interface Name'))
        
        server_allowed = f'{wg_address},::/0' if mikrotik else wg_address

        # Allow everything if nothing was specified
        if not (allowed := get_info('Allowed IPs')):
            allowed = '0.0.0.0/0, ::/0'
        
        # This Peer info is of the server for the local host
        client_peer = Peer(client, server, allowed, 25, psk)
        
        if mikrotik:
            mikrotik_script += f'\n{client_peer.mikrotik()}'

        # This Peer info is of the host for the remote server
        server_peers.append(Peer(
            server, client, server_allowed, preshared_key=psk, name=hostname
        ))

        
        client_configs[hostname] = ConfigFile(client, client_peer)

    server_config = ConfigFile(server, server_peers)

    # Create the nested folders needed for capturing the configs
    makedirs('output', exist_ok=True)
    makedirs(path.join('output', server.Hostname), exist_ok=True)
    makedirs(path.join('output', server.Hostname, 'clients'), exist_ok=True)

    server_dir = path.join('output', server.Hostname)

    with open(path.join(server_dir, f'server.conf'), 'w') as server_file:
        server_file.write(str(server_config))

    if mikrotik:
        with open(path.join(server_dir, 'mikrotik_server.txt'), 'w') as mikrotik_file:
            mikrotik_file.write(mikrotik_script + '\n')

    # write all the clients

    for hostname, config in client_configs.items():
        host_file = f'{hostname.replace(' ','_')}.conf'
        with open(path.join(server_dir, 'clients', host_file), 'w') as client_file:
            client_file.write(str(config)) 


def create_pair(first: Interface, second: Interface,
                allowed: str = ''):
    """"""
    if not allowed:
        allowed = '0.0.0.0/0, ::/0'

    psk = generate_preshared_key()

    second_as_peer = Peer(first, second, allowed, preshared_key=psk, name=second.Hostname)
    first_as_peer = Peer(second, first, allowed, preshared_key=psk, name=first.Hostname)

    first_config = ConfigFile(first, second_as_peer)
    second_config = ConfigFile(second, first_as_peer)

    makedirs('output', exist_ok=True)

    for host_config in [first_config, second_config]:
        folder_path = path.join('output', host_config.interface.Hostname)
        makedirs(folder_path, exist_ok=True)

        file_path = path.join(folder_path, 'wg.conf')

        with open(file_path, 'w') as config_file:
            config_file.write(str(host_config))

        mt_path = path.join(folder_path, 'mt.rsc')
        with open(mt_path, 'w') as mt_config:
            mt_script = host_config.interface.mikrotik() + '\n' + host_config.peers[0].mikrotik()
            mt_config.write(mt_script)
            

def clients_main(csv_path: str = None):
    """
    Currently ingests the client info from `clients.csv`
    Server info is populated via the keyword args
    """
    csv_path = 'clients.csv' if csv_path is None else csv_path

    server_kwargs = {
        'address': None,
        'endpoint': None,
        'hostname': None,
        'interface_name': None,
        'listen_port': None,
    }

    server = Interface(**server_kwargs)
    ingest_client_csv(server, csv_path)

def pair_main():
    """
    Create a pair of configs for site-to-site purposes
    """
    # POPULATE THE INFO NEEDED FIRST
    first = Interface()
    second = Interface()
    create_pair(first, second)

if __name__ == '__main__':
    clients_main('sff_clients.csv')
    # pair_main()