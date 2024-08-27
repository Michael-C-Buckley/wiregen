"""
WireGen Interface Module
"""


from re import search
from typing import Optional

from wiregen.common import generate_wireguard_keypair


class Interface:
    """
    Container for Wireguard Interface data
    """

    def __init__(self,
                 address: str,
                 endpoint: Optional[str] = None,
                 hostname: Optional[str] = None,
                 interface_name: Optional[str] = None,
                 private_key: Optional[str] = None,
                 public_key: Optional[str] = None,
                 listen_port: int = 51820,
                 dns: Optional[str] = None,
                 table: Optional[int] = None,
                 mtu: Optional[int] = None,
                 pre_up: Optional[str] = None,
                 post_up: Optional[str] = None,
                 pre_down: Optional[str] = None,
                 post_down: Optional[str] = None) -> None:
        
        keys_map = {
            (False, False): lambda: generate_wireguard_keypair(),
            (True, False): lambda: generate_wireguard_keypair(private_key),
            (True, True): lambda: (private_key, public_key),
        }

        key_tuple = (bool(private_key), bool(public_key))

        if (result_function := keys_map.get(key_tuple)):
            self.PrivateKey, self.PublicKey = result_function()
        else:
            print('WARNING: Public key supplied without private key, regenerating new pair')
            self.PrivateKey, self.PublicKey = generate_wireguard_keypair()

        self.Endpoint = endpoint
        self.InterfaceName = interface_name
        self.Address = address
        self.Hostname = hostname
        self.DNS = dns
        self.Table = table

        if listen_port < 0 or listen_port > 65535:
            raise ValueError(f'Invalid Listen Port: {listen_port}')
        elif listen_port < 1024:
            print(f'**WARNING: Listen port ({listen_port}) is in the well-known port range, it is suggested to use a port above 1024 or higher')


        if mtu is not None:
            if 63 > mtu > 65535:
                raise ValueError(f'Invalid MTU: {mtu}')
            if mtu > 9216:
                print(f'**WARNING: MTU ({mtu}) above common Jumbo frame size, this may not work unless you know what you are doing **')

        self.MTU = mtu
        self.ListenPort = listen_port
        self.PreUp = pre_up
        self.PostUp = post_up
        self.PreDown = pre_down
        self.PostDown = post_down

    def __str__(self) -> str:
        """
        Render the interface info as a config template string
        """
        output = [f'[Interface]']

        for item in ['Hostname', 'Endpoint', 'InterfaceName', 'PublicKey']:
            if not (value := getattr(self, item)):
                continue
            output.append(f'# {item} = {value}')

        for item in ['PrivateKey', 'Address', 'ListenPort', 'DNS', 'Table',
                     'MTU', 'PreUp', 'PostUp', 'PreDown', 'PostDown']:
            if not (value := getattr(self, item)):
                continue
            output.append(f'{item} = {value}')

        return '\n'.join(output)
    
    def mikrotik(self, comment: str = None, disabled: bool = None,
                 add_fw_rules: bool = True) -> str:
        """
        Renders the Mikrotik CLI command for this new tunnel
        """
        output_str = f'/interface/wireguard/add'

        disabled = 'yes' if disabled is True else None

        if self.InterfaceName is None:
            short_tag = search(r'[a-zA-Z\d+]{4}', self.PublicKey)
            # Log the creation of the name
            self.InterfaceName = f'wg-tunnel-{short_tag.group()}'

        kv_pairs = {
            'name': self.InterfaceName,
            'comment': comment,
            'mtu': self.MTU,
            'disabled': disabled,
            'private-key': f'"{self.PrivateKey}"',
            'listen-port': self.ListenPort,
        }

        for k, v in kv_pairs.items():
            if v is not None:
                output_str += f' {k}={v}'

        # Apply the address
        output_str += f'\n/ip/address/add interface={self.InterfaceName} address={self.Address}'

        if add_fw_rules is True:
            # Open the listening ports on IPv4 and IPv6 for Wireguard interface
            common_fw_str = 'firewall/filter/add chain=input action=accept protocol=udp'
            for proto in ['ip', 'ipv6']:
                output_str += f'\n/{proto}/{common_fw_str} dst-port={self.ListenPort} comment="Wireguard {self.InterfaceName} Listen Port"'

        return output_str