from datamodel import OrderDepth, Listing, TradingState, Observation
from Trader import Trader
from collections import defaultdict

class Backtester:
    def __init__(self, trader_class):
        self.trader = trader_class()
        self.history = []
        self.cumulative_pnl = 0
        
    def create_order_depth(self, buy_orders: dict, sell_orders: dict) -> OrderDepth:
        """Helper method to properly create OrderDepth objects"""
        order_depth = OrderDepth()
        order_depth.buy_orders = buy_orders
        order_depth.sell_orders = {k: -abs(v) for k, v in sell_orders.items()}  # Ensure sell orders are negative
        return order_depth

    def simulate_tick(self, timestamp, order_depths, positions):
        """Simulate a single trading tick"""
        state = TradingState(
            timestamp=timestamp,
            listings={p: Listing(p, p, "SEASHELLS") for p in order_depths},
            order_depths=order_depths,
            position=positions,
            observations=Observation({}, {}),
            own_trades=defaultdict(list),
            market_trades=defaultdict(list),
            traderData=""
        )
        
        orders, conversions, _ = self.trader.run(state)
        
        # Simulate order execution (simplified)
        new_positions = positions.copy()
        pnl_delta = 0
        
        for product in orders:
            for order in orders[product]:
                new_positions[product] = new_positions.get(product, 0) + order.quantity
                # Simplified PnL calculation
                pnl_delta -= order.quantity * order.price
        
        self.cumulative_pnl += pnl_delta
        
        tick_result = {
            "timestamp": timestamp,
            "fair_values": {p: self.trader.calculate_dynamic_fair_value(p, order_depths[p]) 
                          for p in order_depths},
            "orders": orders,
            "positions": new_positions,
            "pnl_delta": pnl_delta,
            "cumulative_pnl": self.cumulative_pnl
        }
        
        self.history.append(tick_result)
        return new_positions

    def print_results(self):
        """Print formatted backtest results"""
        for result in self.history:
            print(f"\n=== Timestamp {result['timestamp']} ===")
            print("Fair Values:")
            for product, value in result["fair_values"].items():
                if value is not None:
                    print(f"  {product}: {value:.2f}")
                else:
                    print(f"  {product}: No valid price")
            
            print("\nOrders:")
            for product, orders in result["orders"].items():
                for order in orders:
                    action = "BUY" if order.quantity > 0 else "SELL"
                    print(f"  {action} {abs(order.quantity)} {product} @ {order.price}")
            
            print("\nPositions:")
            for product, pos in result["positions"].items():
                print(f"  {product}: {pos}")
            
            print(f"\nPnL Delta: {result['pnl_delta']:.2f}")
            print(f"Cumulative PnL: {result['cumulative_pnl']:.2f}")

def create_test_timeline():
    """Create test timeline with properly initialized OrderDepth objects"""
    timeline = []
    
    # Timestamp 1000
    resin_depth = OrderDepth()
    resin_depth.buy_orders = {9998: 5, 9997: 3}
    resin_depth.sell_orders = {10002: -4, 10003: -2}
    
    kelp_depth = OrderDepth()
    kelp_depth.buy_orders = {1500: 10, 1498: 5}
    kelp_depth.sell_orders = {1505: -8, 1506: -4}
    
    timeline.append({
        "timestamp": 1000,
        "order_depths": {
            "RAINFOREST_RESIN": resin_depth,
            "KELP": kelp_depth
        }
    })
    
    # Timestamp 1001
    resin_depth = OrderDepth()
    resin_depth.buy_orders = {9999: 6, 9998: 4}
    resin_depth.sell_orders = {10001: -5, 10002: -3}
    
    kelp_depth = OrderDepth()
    kelp_depth.buy_orders = {1502: 8, 1501: 6}
    kelp_depth.sell_orders = {1504: -7, 1505: -5}
    
    timeline.append({
        "timestamp": 1001,
        "order_depths": {
            "RAINFOREST_RESIN": resin_depth,
            "KELP": kelp_depth
        }
    })
    
    return timeline

def run_backtest():
    print("=== Starting Backtest ===")
    backtester = Backtester(Trader)
    
    # Initialize positions
    test_timeline = create_test_timeline()
    positions = {product: 0 for product in test_timeline[0]["order_depths"]}
    
    # Run through each timestamp
    for tick in test_timeline:
        positions = backtester.simulate_tick(
            tick["timestamp"],
            tick["order_depths"],
            positions
        )
    
    # Print final results
    backtester.print_results()

if __name__ == "__main__":
    run_backtest()