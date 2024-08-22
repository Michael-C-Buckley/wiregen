"""
WireGen Common Functions
"""

# Python Modules
from re import match
from subprocess import check_output

def validate_key(key: str) -> str:
    if not match(r'^[A-Za-z0-9+/]{42}[AEIMQUYcgkosw480]=$', key):
        raise ValueError(f'Supplied Wireguard key is not a valid key\n SUPPLIED KEY: {key}')
    return key

def generate_wireguard_keypair(private_key: str = None) -> tuple[str, str]:
    """
    Generate a Wireguard key pair, takes an optional supplied private and will create the matching public key
    """
    if private_key is None:
        private_key = check_output(['wg', 'genkey']).strip().decode('utf-8')
    else:
        validate_key(private_key)
    public_key = check_output(['wg', 'pubkey'], input=private_key.encode()).strip().decode('utf-8')
    return private_key, public_key  

def generate_preshared_key() -> str:
    return check_output(['wg', 'genpsk']).decode('utf-8').strip()

def gen_keys():
    private_key, public_key = generate_wireguard_keypair()
    print(f"Private Key: {private_key}")
    print(f"Public Key: {public_key}")