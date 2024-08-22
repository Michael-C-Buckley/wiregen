"""
WIREGEN
"""

from csv import reader
from io import StringIO
from os import path, makedirs

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

    # a script designed to be pasted into a Mirkotik CLI
    if mikrotik:
        mikrotik_script = server.mikrotik()

    for client_data in client_csv:
        get_info = lambda x: client_data[invert_header[x]]

        preshared_key = generate_preshared_key()

        wg_address = get_info('Interface Address')
        hostname = get_info('Hostname')

        client = Interface(wg_address, hostname=hostname, interface_name=get_info('Interface Name'))
        
        # server_allowed = f'{wg_address},::/0'
        server_allowed = wg_address

        # Allow everything if nothing was specified
        if not (allowed := get_info('Allowed IPs')):
            allowed = '0.0.0.0/0, ::/0'
        
        # This Peer info is of the server for the local host
        client_peer = Peer(client, server, allowed, 25, preshared_key)
        
        if mikrotik:
            mikrotik_script += f'\n{client_peer.mikrotik()}'

        # This Peer info is of the host for the remote server
        server_peers.append(Peer(server, client, wg_address,
                                 preshared_key=preshared_key,
                                 name=hostname))

        
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
        with open(path.join(server_dir, 'clients', f'{hostname}.conf'), 'w') as client_file:
            client_file.write(str(config)) 





if __name__ == '__main__':
    """
    Currently ingests the client info from `clients.csv`
    Server info is populated via the keyword args
    """

    server_kwargs = {
        'address': None,
        'endpoint': None,
        'hostname': None,
        'interface_name': None,
        'listen_port': None,
    }
    server = Interface(**server_kwargs)
    ingest_client_csv(server, 'clients.csv')