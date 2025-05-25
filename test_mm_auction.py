import asyncio
import time
import random
from typing import List, Dict
import aiohttp
import statistics
from datetime import datetime

class AuctionTester:
    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        # Load test config
        num_requests: int = 100,
        concurrent_requests: int = 10,
        # Latency test config
        latency_duration: int = 60,  # 1 minute
        # Stress test config
        initial_concurrent: int = 10,
        max_concurrent: int = 100,
        step_size: int = 10,
        step_duration: int = 30,  # 30 seconds per step
    ):
        self.base_url = base_url
        # Load test params
        self.num_requests = num_requests
        self.concurrent_requests = concurrent_requests
        # Latency test params
        self.latency_duration = latency_duration
        # Stress test params
        self.initial_concurrent = initial_concurrent
        self.max_concurrent = max_concurrent
        self.step_size = step_size
        self.step_duration = step_duration
        
        self.results = {
            "load_test": [],
            "latency_test": [],
            "stress_test": {}
        }

    async def make_auction_request(self, request_id: int) -> Dict:
        """Make a single auction request"""
        start_time = time.time()
        
        auction_data = {
            "token_in": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",  # WETH
            "token_out": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",  # USDC
            "amount_in": str(random.randint(100000000000000000, 1000000000000000000)),  # 0.1-1 WETH
            "min_amount_out": str(random.randint(1700000000, 1900000000)),  # 1700-1900 USDC
            "is_market": random.choice([True, False])
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/jit-auction",
                    json=auction_data
                ) as response:
                    response_time = time.time() - start_time
                    status = response.status
                    response_data = await response.json()
                    
                    return {
                        "request_id": request_id,
                        "status": status,
                        "response_time": response_time,
                        "response_data": response_data,
                        "timestamp": datetime.now().isoformat()
                    }
        except Exception as e:
            return {
                "request_id": request_id,
                "status": "error",
                "error": str(e),
                "response_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }

    async def run_load_test(self):
        """Run load test"""
        print("\n=== Running Load Test ===")
        print(f"Total requests: {self.num_requests}")
        print(f"Concurrent requests: {self.concurrent_requests}")
        
        start_time = time.time()
        sem = asyncio.Semaphore(self.concurrent_requests)
        
        async def bounded_request(request_id: int):
            async with sem:
                result = await self.make_auction_request(request_id)
                self.results["load_test"].append(result)
        
        tasks = [bounded_request(i) for i in range(self.num_requests)]
        await asyncio.gather(*tasks)
        
        # Calculate statistics
        total_time = time.time() - start_time
        response_times = [r["response_time"] for r in self.results["load_test"]]
        successful_requests = len([r for r in self.results["load_test"] if r["status"] == 200])
        
        print("\nLoad Test Results:")
        print(f"Total time: {total_time:.2f}s")
        print(f"Successful requests: {successful_requests}/{self.num_requests}")
        print(f"Average response time: {statistics.mean(response_times):.3f}s")
        print(f"Requests per second: {self.num_requests / total_time:.2f}")

    async def run_latency_test(self):
        """Run latency test"""
        print("\n=== Running Latency Test ===")
        print(f"Duration: {self.latency_duration}s")
        
        start_time = time.time()
        request_id = 0
        
        while time.time() - start_time < self.latency_duration:
            result = await self.make_auction_request(request_id)
            self.results["latency_test"].append(result)
            
            if request_id % 10 == 0:
                elapsed = time.time() - start_time
                print(f"Progress: {elapsed:.1f}s / {self.latency_duration}s")
            
            request_id += 1
            await asyncio.sleep(1.0)  # 1 request per second
        
        # Calculate statistics
        response_times = [r["response_time"] for r in self.results["latency_test"]]
        successful_requests = len([r for r in self.results["latency_test"] if r["status"] == 200])
        
        print("\nLatency Test Results:")
        print(f"Total requests: {len(self.results['latency_test'])}")
        print(f"Successful requests: {successful_requests}")
        print(f"Average response time: {statistics.mean(response_times):.3f}s")
        print(f"95th percentile: {sorted(response_times)[int(len(response_times) * 0.95)]:.3f}s")

    async def run_stress_test(self):
        """Run stress test"""
        print("\n=== Running Stress Test ===")
        print(f"Initial concurrent: {self.initial_concurrent}")
        print(f"Max concurrent: {self.max_concurrent}")
        print(f"Step size: {self.step_size}")
        print(f"Step duration: {self.step_duration}s")
        
        current_concurrent = self.initial_concurrent
        
        while current_concurrent <= self.max_concurrent:
            print(f"\nTesting {current_concurrent} concurrent requests...")
            
            results = []
            start_time = time.time()
            request_id = 0
            
            # Run stress step
            while time.time() - start_time < self.step_duration:
                tasks = [
                    self.make_auction_request(request_id + i)
                    for i in range(current_concurrent)
                ]
                step_results = await asyncio.gather(*tasks)
                results.extend(step_results)
                request_id += current_concurrent
            
            self.results["stress_test"][current_concurrent] = results
            
            # Calculate statistics
            response_times = [r["response_time"] for r in results]
            successful_requests = len([r for r in results if r["status"] == 200])
            
            print(f"Results for {current_concurrent} concurrent requests:")
            print(f"Successful requests: {successful_requests}/{len(results)}")
            print(f"Average response time: {statistics.mean(response_times):.3f}s")
            print(f"Requests per second: {len(results) / self.step_duration:.2f}")
            
            # Check if system is still responding well
            if statistics.mean(response_times) > 1.0 or successful_requests / len(results) < 0.95:
                print("\nSystem showing signs of stress. Stopping test.")
                break
            
            current_concurrent += self.step_size

    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("Starting comprehensive market maker auction tests...")
        
        # Run load test
        await self.run_load_test()
        
        # Run latency test
        await self.run_latency_test()
        
        # Run stress test
        await self.run_stress_test()
        
        # Save all results
        with open("auction_test_results.json", "w") as f:
            import json
            json.dump(self.results, f, indent=2)
        
        print("\nAll tests completed. Results saved to auction_test_results.json")

async def main():
    # Configuration with reasonable defaults for quick testing
    tester = AuctionTester(
        base_url="http://localhost:8080",
        # Load test: 100 requests, 10 concurrent
        num_requests=100,
        concurrent_requests=10,
        # Latency test: 1 minute
        latency_duration=60,
        # Stress test: 10 to 100 concurrent, steps of 10
        initial_concurrent=10,
        max_concurrent=100,
        step_size=10,
        step_duration=30
    )
    
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 