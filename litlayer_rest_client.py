import json
import time
import requests
from typing import Dict, Optional
from key_generator import KeyGenerator

class LitLayerRestClient:
    def __init__(self, base_url: str = "https://api.litlayer.com", api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.key_generator = KeyGenerator(base_url)
        self.session_data = None

    def generate_session(self, wallet_address: str, agent_address: str) -> Dict:
        """
        Generate a new session with trading key and signature.
        
        Args:
            wallet_address: The wallet address
            agent_address: The agent address
            
        Returns:
            Dict containing session data
        """
        # Generate trading key
        trading_key = self.key_generator.generate_trading_key(agent_address)
        
        # Prepare and sign EIP-712 data
        eip712_data = self.key_generator.prepare_eip712_data(
            agent_address=agent_address,
            platform="turbox",
            environment="Devnet"
        )
        signature = self.key_generator.sign_eip712_data(eip712_data, trading_key)
        
        # Store session data
        self.session_data = {
            "wallet_address": wallet_address,
            "agent_address": agent_address,
            "trading_key": trading_key,
            "eip712_data": eip712_data,
            "signature": signature
        }
        
        return self.session_data

    def make_signed_request(
        self,
        method: str,
        endpoint: str,
        payload: Dict,
        use_session: bool = True
    ) -> Dict:
        """
        Make a signed request to the API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., 'v1/withdraw/submit')
            payload: Request payload
            use_session: Whether to use session signature
            
        Returns:
            API response
        """
        if not self.api_key:
            raise Exception("API key not set")
            
        url = f"{self.base_url}/{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key
        }
        
        # If using session, add signature to payload
        if use_session and self.session_data:
            payload["signature"] = self.session_data["signature"]
        
        response = requests.request(method, url, json=payload, headers=headers)
        
        if response.status_code != 200:
            error_msg = f"Request failed: {response.text}"
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_msg = f"API error: {error_data['error']}"
            except:
                pass
            raise Exception(error_msg)
            
        return response.json()

    def submit_withdrawal(
        self,
        token_address: str,
        amount: str,
        recipient_address: str
    ) -> Dict:
        """
        Submit a withdrawal request.
        
        Args:
            token_address: Token contract address
            amount: Amount to withdraw
            recipient_address: Recipient address
            
        Returns:
            Withdrawal response
        """
        payload = {
            "token_address": token_address,
            "amount": amount,
            "recipient_address": recipient_address
        }
        
        return self.make_signed_request("POST", "v1/withdraw/submit", payload)

    def create_order(
        self,
        token_in: str,
        token_out: str,
        amount_in: str,
        min_amount_out: str,
        is_market: bool = False
    ) -> Dict:
        """
        Create a new order.
        
        Args:
            token_in: Input token address
            token_out: Output token address
            amount_in: Input amount
            min_amount_out: Minimum output amount
            is_market: Whether this is a market order
            
        Returns:
            Order creation response
        """
        payload = {
            "token_in": token_in,
            "token_out": token_out,
            "amount_in": amount_in,
            "min_amount_out": min_amount_out,
            "is_market": is_market
        }
        
        return self.make_signed_request("POST", "v1/order/create", payload)

def main():
    """Example usage of the LitLayerRestClient"""
    # Initialize client
    client = LitLayerRestClient(
        base_url="https://api.litlayer.com",
        api_key="your_api_key"
    )
    
    # Example addresses
    wallet_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    agent_address = "0xd28ac95d6D5Ba255816043200DD502A8EE5dD03C"
    
    try:
        # 1. Generate session
        print("Generating session...")
        session = client.generate_session(wallet_address, agent_address)
        print(f"Session generated: {json.dumps(session, indent=2)}")
        
        # 2. Submit withdrawal
        print("\nSubmitting withdrawal...")
        withdrawal = client.submit_withdrawal(
            token_address="0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",  # WETH on Arbitrum
            amount="1000000000000000000",  # 1 WETH
            recipient_address=wallet_address
        )
        print(f"Withdrawal response: {json.dumps(withdrawal, indent=2)}")
        
        # 3. Create order
        print("\nCreating order...")
        order = client.create_order(
            token_in="0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",  # WETH
            token_out="0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",  # USDC
            amount_in="1000000000000000000",  # 1 WETH
            min_amount_out="1800000000",  # 1800 USDC
            is_market=True
        )
        print(f"Order response: {json.dumps(order, indent=2)}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 