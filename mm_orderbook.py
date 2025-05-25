import json
import time
import asyncio
from typing import Dict, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from litlayer_rest_client import LitLayerRestClient

class OrderConfig(BaseModel):
    """Configuration for order placement"""
    token_in: str = Field(..., description="Input token address")
    token_out: str = Field(..., description="Output token address")
    min_order_size: str = Field(..., description="Minimum order size in input token")
    max_order_size: str = Field(..., description="Maximum order size in input token")
    price_spread: float = Field(..., description="Price spread percentage")
    max_orders: int = Field(..., description="Maximum number of orders per side")

class MarketData(BaseModel):
    """Market data structure"""
    timestamp: int
    best_bid: str
    best_ask: str
    last_price: str
    volume_24h: str

class OrderBookMM:
    def __init__(
        self,
        base_url: str = "https://api.litlayer.com",
        api_key: str = None,
        wallet_address: str = None,
        agent_address: str = None,
        order_config: OrderConfig = None,
        pending_order_interval: int = 30,  # seconds
        cancel_order_interval: int = 10,   # seconds
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.wallet_address = wallet_address
        self.agent_address = agent_address
        self.order_config = order_config
        self.pending_order_interval = pending_order_interval
        self.cancel_order_interval = cancel_order_interval
        
        # Initialize client
        self.client = LitLayerRestClient(base_url, api_key)
        self.session_data = None
        
        # State management
        self.active_orders: Dict[str, Dict] = {}  # order_id -> order_data
        self.market_data: Optional[MarketData] = None
        self.inventory: Dict[str, str] = {}  # token_address -> amount
        
        # Task control
        self.running = False
        self.pending_order_task = None
        self.cancel_order_task = None
        self._lock = asyncio.Lock()  # For thread-safe operations

    def generate_session(self) -> Dict:
        """Generate a new session with trading key and signature"""
        if not self.wallet_address or not self.agent_address:
            raise Exception("Wallet address and agent address must be set")
            
        self.session_data = self.client.generate_session(
            self.wallet_address,
            self.agent_address
        )
        return self.session_data

    async def check_inventory(self) -> Dict[str, str]:
        """
        Check current inventory levels.
        This is a placeholder - implement actual inventory checking logic.
        """
        # Placeholder: In reality, this would query your inventory system
        return {
            self.order_config.token_in: "10000000000000000000",  # 10 tokens
            self.order_config.token_out: "2000000000"  # 2000 tokens
        }

    async def get_market_data(self) -> MarketData:
        """
        Get latest market data.
        This is a placeholder - implement actual market data fetching.
        """
        # Placeholder: In reality, this would fetch from your data source
        return MarketData(
            timestamp=int(time.time()),
            best_bid="1750000000",  # 1750
            best_ask="1850000000",  # 1850
            last_price="1800000000",  # 1800
            volume_24h="100000000000000000000"  # 100 tokens
        )

    async def place_order(
        self,
        token_in: str,
        token_out: str,
        amount_in: str,
        min_amount_out: str,
        is_market: bool = False
    ) -> Dict:
        """Place a new order"""
        return await self.client.create_order(
            token_in=token_in,
            token_out=token_out,
            amount_in=amount_in,
            min_amount_out=min_amount_out,
            is_market=is_market
        )

    async def cancel_order(self, order_id: str) -> Dict:
        """Cancel an existing order"""
        # Placeholder: Implement actual order cancellation
        async with self._lock:
            if order_id in self.active_orders:
                del self.active_orders[order_id]
        return {"status": "cancelled", "order_id": order_id}

    async def pending_order_task(self):
        """Task to manage pending orders"""
        while self.running:
            try:
                # 1. Check inventory
                self.inventory = await self.check_inventory()
                
                # 2. Get market data
                self.market_data = await self.get_market_data()
                
                # 3. Calculate order sizes based on inventory and market data
                # This is a simplified example - implement your actual logic
                async with self._lock:
                    if len(self.active_orders) < self.order_config.max_orders:
                        # Place a new order
                        order = await self.place_order(
                            token_in=self.order_config.token_in,
                            token_out=self.order_config.token_out,
                            amount_in=self.order_config.min_order_size,
                            min_amount_out=str(int(self.market_data.last_price) * 0.99),  # 1% below market
                            is_market=False
                        )
                        
                        if "order_id" in order:
                            self.active_orders[order["order_id"]] = order
                
            except Exception as e:
                print(f"Error in pending order task: {e}")
            
            await asyncio.sleep(self.pending_order_interval)

    async def cancel_order_task(self):
        """Task to manage order cancellations"""
        while self.running:
            try:
                # 1. Get latest market data
                self.market_data = await self.get_market_data()
                
                # 2. Check each active order
                async with self._lock:
                    for order_id, order in list(self.active_orders.items()):
                        # Example cancellation logic:
                        # Cancel if price moved more than 2% from order price
                        order_price = int(order.get("price", 0))
                        current_price = int(self.market_data.last_price)
                        price_diff_pct = abs(order_price - current_price) / current_price
                        
                        if price_diff_pct > 0.02:  # 2% threshold
                            await self.cancel_order(order_id)
                
            except Exception as e:
                print(f"Error in cancel order task: {e}")
            
            await asyncio.sleep(self.cancel_order_interval)

    async def start(self):
        """Start the market maker"""
        if not self.session_data:
            self.generate_session()
            
        self.running = True
        
        # Start tasks
        self.pending_order_task = asyncio.create_task(self.pending_order_task())
        self.cancel_order_task = asyncio.create_task(self.cancel_order_task())
        
        print("Market maker started")
        print(f"Pending order interval: {self.pending_order_interval}s")
        print(f"Cancel order interval: {self.cancel_order_interval}s")

    async def stop(self):
        """Stop the market maker"""
        self.running = False
        
        # Cancel tasks
        if self.pending_order_task:
            self.pending_order_task.cancel()
            try:
                await self.pending_order_task
            except asyncio.CancelledError:
                pass
                
        if self.cancel_order_task:
            self.cancel_order_task.cancel()
            try:
                await self.cancel_order_task
            except asyncio.CancelledError:
                pass
            
        print("Market maker stopped")

async def main():
    """Example usage of the OrderBookMM"""
    # Configuration
    API_KEY = "your_api_key"
    WALLET_ADDRESS = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    AGENT_ADDRESS = "0xd28ac95d6D5Ba255816043200DD502A8EE5dD03C"
    
    # Order configuration
    order_config = OrderConfig(
        token_in="0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",  # WETH
        token_out="0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",  # USDC
        min_order_size="100000000000000000",  # 0.1 WETH
        max_order_size="1000000000000000000",  # 1 WETH
        price_spread=0.02,  # 2%
        max_orders=5
    )
    
    try:
        # Initialize market maker
        mm = OrderBookMM(
            base_url="https://api.litlayer.com",
            api_key=API_KEY,
            wallet_address=WALLET_ADDRESS,
            agent_address=AGENT_ADDRESS,
            order_config=order_config,
            pending_order_interval=30,  # 30 seconds
            cancel_order_interval=10    # 10 seconds
        )
        
        # Start market maker
        await mm.start()
        
        # Keep the main task alive
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping market maker...")
            await mm.stop()
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 