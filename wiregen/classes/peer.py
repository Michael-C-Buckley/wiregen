from re import sub

from wiregen.classes.interface import Interface

class Peer:
    """
    Container for Wireguard Peer data
    """

    def __init__(self,
                 local_interface: Interface,
                 remote_interface: Interface,
                 allowed_ips: str,
                 persistent_keepalive: int = None,
                 preshared_key: str = None,
                 name: str = None) -> None:
        

        # Info from the remote host
        self.local_interface = local_interface
        self.remote_peer = remote_interface
        self.PublicKey = remote_interface.PublicKey
        self.PrivateKey = local_interface.PrivateKey
        self.PeerIP = remote_interface.Address
        self.Name = name if name is not None else remote_interface.Hostname

        if remote_interface.Endpoint:
            self.Endpoint = f'{remote_interface.Endpoint}:{remote_interface.ListenPort}'
        else:
            self.Endpoint = None

        # TO ADD: Allow IP parse and verification

        self.PersistentKeepalive = persistent_keepalive
        
        self.AllowedIPs = allowed_ips
        self.PresharedKey = preshared_key

    def __str__(self) -> str:
        """
        Produce the config format of a peer
        """
        output = [f'[Peer]']

        if self.Name:
            output.append(f'# Name = {self.Name}')

        if self.PeerIP:
            output.append(f'# Peer IP = {self.PeerIP}')

        for item in ['PublicKey', 'AllowedIPs', 'Endpoint', 'PresharedKey', 'PersistentKeepalive']:
            if not (value := getattr(self, item)):
                continue

            output.append(f'{item} = {value}')

        return '\n'.join(output)
    
    def mikrotik(self, client: bool = True, allow_all_ipv6: bool = True) -> str:
        """
        Renders the Mikrotik CLI command for this peer
        """
        comment = f'comment="{self.local_interface.Hostname}"'
        intf = f'interface={self.remote_peer.InterfaceName}'
        output_str = f'/interface/wireguard/peers/add {intf} {comment}'

        # Add a dash between words and lower case the phrase
        for item in ['PublicKey', 'PrivateKey', 'PresharedKey', 'PersistentKeepalive']:
            output_str += f' {sub(r'(?<!^)(?=[A-Z])', '-', item).lower()}="{getattr(self,item)}"'

        # These attributes don't match exactly and need to be replaced
        allowed = f'"{self.local_interface.Address},::/0"' if allow_all_ipv6 else f'"{self.local_interface.Address}"'
        if client is True:
            # This is a client and not another server
            output_str += f' allowed-address={allowed}'
        else:    
            # This is to another server
            matching_map = {
                'AllowedIPs': 'allowed-address',
                'Endpoint': 'endpoint-address',
            }

            for k, v in matching_map.items():
                if (value := getattr(self,k)):
                    output_str += f' {v}="{value}"'

        return output_str