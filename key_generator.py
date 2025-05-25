import os
import json
import hashlib
import secrets
import time
import requests
from typing import Dict, Tuple
from eth_keys.datatypes import PrivateKey
from eth_utils import keccak, to_hex, to_bytes
from eth_abi import encode_abi
from eth_abi.abi import encode_typed
from cryptography.fernet import Fernet
import base58

class KeyGenerator:
    def __init__(self, base_url: str = "https://api.litlayer.com"):
        self.base_url = base_url.rstrip('/')
        self.storage_dir = ".keys"
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
        
        # EIP-712 domain data
        self.domain = {
            "name": "LitLayer",
            "version": "v1",
            "chainId": 42161,  # Arbitrum
            "verifyingContract": "0x0000000000000000000000000000000000000000",
            "salt": "0x0000000000000000000000000000000000000000000000000000000000000000"
        }
        
        # EIP-712 types
        self.types = {
            "Agent": [
                {"name": "litLayer", "type": "string"},
                {"name": "agentAddress", "type": "address"},
                {"name": "platform", "type": "string"},
                {"name": "expiryTime", "type": "uint256"}
            ],
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
                {"name": "salt", "type": "bytes32"}
            ]
        }

    def generate_trading_key(self, agent_address: str) -> str:
        """
        Generate a private key for signing trades on behalf of the agent address.
        This key will be used for 1-click trading without requiring user signatures.
        
        Args:
            agent_address: The agent address to generate a trading key for
            
        Returns:
            Private key in hex format
        """
        # Generate a truly random private key using ECDSA Secp256k1
        private_key = PrivateKey(secrets.token_bytes(32))
        return f"0x{private_key.to_hex()}"

    def prepare_eip712_data(
        self,
        agent_address: str,
        platform: str = "turbox",
        environment: str = "Devnet"
    ) -> Dict:
        """
        Prepare EIP-712 structured data for agent registration.
        
        Args:
            agent_address: The agent address to register
            platform: Platform ID (default: "turbox")
            environment: Environment (Devnet, Testnet, Mainnet)
            
        Returns:
            Dict containing EIP-712 domain data and message
        """
        # Calculate expiry time (24 hours from now)
        expiry_time = int(time.time()) + 86400
        
        # Prepare EIP-712 message
        message = {
            "litLayer": environment,
            "agentAddress": agent_address,
            "platform": platform,
            "expiryTime": expiry_time
        }
        
        return {
            "domain": self.domain,
            "types": self.types,
            "message": message
        }

    def encode_typed_data(self, data: Dict) -> bytes:
        """
        Encode the EIP-712 typed data according to the specification.
        
        Args:
            data: The EIP-712 data to encode
            
        Returns:
            The encoded data as bytes
        """
        # Encode domain separator
        domain_separator = self._encode_domain(data["domain"])
        
        # Encode the message
        message_hash = self._encode_message(data["types"], data["message"])
        
        # Combine domain separator and message hash
        return keccak(b"\x19\x01" + domain_separator + message_hash)

    def _encode_domain(self, domain: Dict) -> bytes:
        """Encode the domain separator"""
        return keccak(encode_typed(
            self.types["EIP712Domain"],
            [
                domain["name"],
                domain["version"],
                domain["chainId"],
                domain["verifyingContract"],
                domain["salt"]
            ]
        ))

    def _encode_message(self, types: Dict, message: Dict) -> bytes:
        """Encode the message data"""
        return keccak(encode_typed(
            types["Agent"],
            [
                message["litLayer"],
                message["agentAddress"],
                message["platform"],
                message["expiryTime"]
            ]
        ))

    def sign_eip712_data(self, eip712_data: Dict, private_key: str) -> str:
        """
        Sign the EIP-712 structured data using eth_signTypedData.
        
        Args:
            eip712_data: The EIP-712 data to sign
            private_key: The private key to sign with
            
        Returns:
            Signature in hex format
        """
        # Convert private key to bytes
        private_key_bytes = bytes.fromhex(private_key[2:])
        private_key_obj = PrivateKey(private_key_bytes)
        
        # Encode the typed data
        encoded_data = self.encode_typed_data(eip712_data)
        
        # Sign the encoded data
        signature = private_key_obj.sign_msg_hash(encoded_data)
        return signature.to_hex()

    def submit_exchange_request(
        self,
        agent_address: str,
        platform: str,
        chain_id: int,
        expiry_time: int,
        signature: str,
        api_key: str
    ) -> Dict:
        """
        Submit the exchange request to /v1/exchange.
        
        Args:
            agent_address: The agent address
            platform: Platform ID
            chain_id: Chain ID (e.g., 42161 for Arbitrum)
            expiry_time: Expiry timestamp
            signature: The EIP-712 signature
            api_key: API key for authentication
            
        Returns:
            Dict containing the response from the API
            
        Raises:
            Exception: If the request fails or returns an error
        """
        # Prepare request payload
        payload = {
            "proxy_address": agent_address,
            "platform": platform,
            "chain_id": chain_id,
            "expiry_time": expiry_time,
            "signature": signature
        }
        
        # Make API request
        url = f"{self.base_url}/v1/exchange"
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': api_key
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        # Check response status
        if response.status_code != 200:
            error_msg = f"Failed to submit exchange request: {response.text}"
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_msg = f"Exchange request failed: {error_data['error']}"
            except:
                pass
            raise Exception(error_msg)
            
        # Return the raw response
        return response.json()

    def save_session_keys(self, wallet_address: str, session_id: str, key_data: Dict):
        """Save session keys to storage"""
        file_path = os.path.join(self.storage_dir, f"{wallet_address}_{session_id}.key")
        with open(file_path, "w") as f:
            json.dump(key_data, f)

    def load_session_keys(self, wallet_address: str, session_id: str) -> Dict:
        """Load session keys from storage"""
        file_path = os.path.join(self.storage_dir, f"{wallet_address}_{session_id}.key")
        if not os.path.exists(file_path):
            return None
            
        with open(file_path, "r") as f:
            return json.load(f)

    def delete_session_keys(self, wallet_address: str, session_id: str):
        """Delete stored session keys"""
        file_path = os.path.join(self.storage_dir, f"{wallet_address}_{session_id}.key")
        if os.path.exists(file_path):
            os.remove(file_path)

def main():
    """Example usage of the KeyGenerator"""
    generator = KeyGenerator()
    wallet_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    agent_address = "0xd28ac95d6D5Ba255816043200DD502A8EE5dD03C"  # From configuration
    api_key = "your_api_key"
    
    # 1. Generate trading key for the agent address
    print("Generating trading key...")
    trading_key = generator.generate_trading_key(agent_address)
    print(f"Generated trading key: {trading_key}")
    
    # 2. Prepare EIP-712 data for agent registration
    print("\nPreparing EIP-712 data...")
    eip712_data = generator.prepare_eip712_data(
        agent_address=agent_address,
        platform="turbox",
        environment="Devnet"
    )
    print(f"EIP-712 data: {json.dumps(eip712_data, indent=2)}")
    
    # 3. Sign the EIP-712 data
    print("\nSigning EIP-712 data...")
    signature = generator.sign_eip712_data(eip712_data, trading_key)
    print(f"Signature: {signature}")
    
    # 4. Submit exchange request
    print("\nSubmitting exchange request...")
    try:
        response = generator.submit_exchange_request(
            agent_address=agent_address,
            platform="turbox",
            chain_id=42161,  # Arbitrum
            expiry_time=int(time.time()) + 86400,
            signature=signature,
            api_key=api_key
        )
        print("\nExchange request successful!")
        print(f"Response: {json.dumps(response, indent=2)}")
    except Exception as e:
        print(f"\nError submitting exchange request: {e}")
        return
    
    # 5. Save session data
    session_id = secrets.token_hex(16)
    session_data = {
        "session_id": session_id,
        "wallet_address": wallet_address,
        "agent_address": agent_address,
        "trading_key": trading_key,
        "eip712_data": eip712_data,
        "signature": signature,
        "exchange_response": response
    }
    generator.save_session_keys(wallet_address, session_id, session_data)
    
    # 6. Load session data
    print("\nLoading session data...")
    loaded_keys = generator.load_session_keys(wallet_address, session_id)
    print(f"Loaded session data: {json.dumps(loaded_keys, indent=2)}")

if __name__ == "__main__":
    main() 