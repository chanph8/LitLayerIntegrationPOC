# Market Maker Auction System

A market maker system for handling JIT (Just-In-Time) auctions and order management, built with FastAPI and asyncio. This system is designed to integrate with LitLayer, a new perpetuals DEX that combines CLOB (Central Limit Order Book) with JIT (Just-In-Time) auction model.

## Integration Objectives

This project aims to integrate with LitLayer's trading infrastructure, providing:
- Market making capabilities for perpetual futures
- JIT auction participation
- Order book management
- Performance monitoring and testing

For detailed documentation about LitLayer's market making model, see:
[LitLayer Market Maker Documentation](https://spangle-mile-967.notion.site/LitLayer-Market-Maker-Documentation-CLOB-x-JIT-Model-DRAFT-14a828721b1c81fa83b6fbd02d0fee28?pvs=74)

For integration guidelines, see:
[LitLayer Client-Server Integration Guide](https://spangle-mile-967.notion.site/LitLayer-Client-Server-Integration-Guide-14a828721b1c806a8e11cf47b0acc0d2?pvs=74)

## Features

- **Session Management**: Secure session key generation and management
- **Auction Handling**: JIT auction processing with configurable parameters
- **Order Management**: Automated order placement and cancellation
- **Performance Testing**: Comprehensive test suite for load, latency, and stress testing

## Components

### 1. Market Maker Auction (`mm_auction.py`)
- FastAPI-based server for handling auction requests
- Endpoints for JIT auctions and trade notifications
- CORS middleware for cross-origin requests
- Structured request/response validation using Pydantic models

### 2. Market Maker Orderbook (`mm_orderbook.py`)
- Automated order management system
- Configurable intervals for order updates
- Inventory-based order sizing
- Market data integration
- Asynchronous order placement and cancellation

### 3. Performance Testing Suite (`test_mm_auction.py`)
- Combined load, latency, and stress testing
- Configurable test parameters
- Detailed performance metrics
- JSON result export

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd market-maker-auction
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Starting the Market Maker Server

```bash
python mm_auction.py
```

The server will start on `http://localhost:8080` by default.

### Running the Orderbook Manager

```bash
python mm_orderbook.py
```

### Running Performance Tests

```bash
python test_mm_auction.py
```

## Configuration

### Market Maker Auction Server
- Default port: 8080
- CORS enabled for all origins
- Configurable session parameters

### Orderbook Manager
- Configurable order update intervals
- Customizable inventory thresholds
- Adjustable price movement thresholds

### Performance Testing
- Load test: 100 requests, 10 concurrent
- Latency test: 1 minute duration
- Stress test: 10-100 concurrent requests

## API Endpoints

### JIT Auction
```
POST /jit-auction
```
Request body:
```json
{
    "token_in": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
    "token_out": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
    "amount_in": "1000000000000000000",
    "min_amount_out": "1800000000",
    "is_market": false
}
```

### Trade Notification
```
POST /trade-notification
```
Request body:
```json
{
    "order_id": "123",
    "status": "filled",
    "filled_amount": "1000000000000000000",
    "price": "1800000000"
}
```

## Performance Testing

The test suite includes three types of tests:

1. **Load Test**
   - Measures system performance under normal load
   - Configurable total and concurrent requests
   - Reports throughput and response times

2. **Latency Test**
   - Measures response time consistency
   - Runs for a specified duration
   - Reports percentiles and success rates

3. **Stress Test**
   - Gradually increases load until system shows stress
   - Identifies breaking points
   - Reports performance degradation

Test results are saved to `auction_test_results.json`.

## Development

### Adding New Features
1. Create feature branch
2. Implement changes
3. Add tests
4. Submit pull request

### Running Tests
```bash
python test_mm_auction.py
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Your License]

## Contact

[Your Contact Information] 