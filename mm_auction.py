import json
import time
import requests
from typing import Dict, Optional
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from key_generator import KeyGenerator
from litlayer_rest_client import LitLayerRestClient

# Request/Response Models
class AuctionRequest(BaseModel):
    token_in: str = Field(..., description="Input token address")
    token_out: str = Field(..., description="Output token address")
    amount_in: str = Field(..., description="Input amount")
    min_amount_out: str = Field(..., description="Minimum output amount")
    is_market: bool = Field(False, description="Whether this is a market order")

class AuctionResponse(BaseModel):
    status: str = Field(..., description="Auction status")
    price: str = Field(..., description="Price in output token")
    amount: str = Field(..., description="Amount in input token")
    timestamp: int = Field(..., description="Response timestamp")

class TradeNotification(BaseModel):
    trade_id: str = Field(..., description="Trade ID")
    token_in: str = Field(..., description="Input token address")
    token_out: str = Field(..., description="Output token address")
    amount_in: str = Field(..., description="Input amount")
    amount_out: str = Field(..., description="Output amount")
    price: str = Field(..., description="Execution price")
    timestamp: int = Field(..., description="Trade timestamp")

class NotificationResponse(BaseModel):
    status: str = Field(..., description="Notification status")
    timestamp: int = Field(..., description="Response timestamp")

class MMAuction:
    def __init__(
        self,
        base_url: str = "https://api.litlayer.com",
        api_key: str = None,
        mm_endpoint: str = None
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.mm_endpoint = mm_endpoint
        self.client = LitLayerRestClient(base_url, api_key)
        self.session_data = None
        self.app = FastAPI(
            title="Market Maker Auction API",
            description="API for handling JIT auctions and trade notifications",
            version="1.0.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup routes
        self.setup_routes()

    def register_mm_endpoint(self, agent_address: str, mm_endpoint: str) -> Dict:
        """
        Register the market maker endpoint with the agent.
        This is a placeholder endpoint - replace with actual endpoint when available.
        
        Args:
            agent_address: The agent address
            mm_endpoint: The market maker endpoint to register
            
        Returns:
            Registration response
        """
        if not self.session_data:
            raise Exception("Session not initialized. Call generate_session first.")
            
        payload = {
            "mm_endpoint": mm_endpoint,
            "agent_address": agent_address
        }
        
        # Using the session signature for authentication
        return self.client.make_signed_request(
            "POST",
            f"{agent_address}/register",
            payload
        )

    async def handle_jit_auction(self, auction_data: AuctionRequest) -> AuctionResponse:
        """
        Handle incoming JIT auction requests.
        This is a placeholder for the actual auction logic.
        
        Args:
            auction_data: The auction request data
            
        Returns:
            Auction response
        """
        # Placeholder for actual auction logic
        print(f"Received JIT auction request: {auction_data.dict()}")
        
        # Example response
        return AuctionResponse(
            status="success",
            price="1800000000",  # 1800 USDC
            amount="1000000000000000000",  # 1 WETH
            timestamp=int(time.time())
        )

    async def handle_trade_notification(self, trade_data: TradeNotification) -> NotificationResponse:
        """
        Handle trade notifications.
        This is a placeholder for the actual trade notification handling.
        
        Args:
            trade_data: The trade notification data
            
        Returns:
            Notification response
        """
        # Placeholder for actual trade notification handling
        print(f"Received trade notification: {trade_data.dict()}")
        
        # Example response
        return NotificationResponse(
            status="received",
            timestamp=int(time.time())
        )

    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.post("/jit-auction", response_model=AuctionResponse)
        async def jit_auction(request: AuctionRequest):
            try:
                return await self.handle_jit_auction(request)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
            
        @self.app.post("/trade-notification", response_model=NotificationResponse)
        async def trade_notification(request: TradeNotification):
            try:
                return await self.handle_trade_notification(request)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

    def start_server(self, host: str = "0.0.0.0", port: int = 8080):
        """
        Start the market maker server using uvicorn.
        
        Args:
            host: Server host
            port: Server port
        """
        print(f"Starting market maker server at http://{host}:{port}")
        print("API documentation available at /docs")
        uvicorn.run(self.app, host=host, port=port)

def main():
    """Example usage of the MMAuction program"""
    # Configuration
    API_KEY = "your_api_key"
    WALLET_ADDRESS = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    AGENT_ADDRESS = "0xd28ac95d6D5Ba255816043200DD502A8EE5dD03C"
    MM_ENDPOINT = "http://your-mm-server:8080"  # Replace with your actual MM server endpoint
    
    try:
        # Initialize market maker
        mm = MMAuction(
            base_url="https://api.litlayer.com",
            api_key=API_KEY,
            mm_endpoint=MM_ENDPOINT
        )
        
        # 1. Generate session
        print("Generating session...")
        session = mm.client.generate_session(WALLET_ADDRESS, AGENT_ADDRESS)
        print(f"Session generated: {json.dumps(session, indent=2)}")
        
        # 2. Register MM endpoint
        print("\nRegistering MM endpoint...")
        registration = mm.register_mm_endpoint(AGENT_ADDRESS, MM_ENDPOINT)
        print(f"Registration response: {json.dumps(registration, indent=2)}")
        
        # 3. Start MM server
        print("\nStarting market maker server...")
        mm.start_server()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 