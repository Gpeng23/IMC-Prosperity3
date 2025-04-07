from datamodel import OrderDepth, Order, TradingState
from typing import Dict, List

class Trader:
    def run(self, state: TradingState):
        result = {}
        position_limit = 50  # Position limit for each product
        threshold = 2  # Minimum price difference to trigger trade
        
        for product, order_depth in state.order_depths.items():
            orders: List[Order] = []
            current_position = state.position.get(product, 0)
            
            # Calculate fair value as midpoint between best bid and ask
            best_bid = max(order_depth.buy_orders.keys()) if order_depth.buy_orders else None
            best_ask = min(order_depth.sell_orders.keys()) if order_depth.sell_orders else None
            
            if best_bid is None or best_ask is None:
                continue  # Skip if no orders on one side
                
            fair_value = (best_bid + best_ask) / 2
            
            # Buy logic: if best ask is significantly below fair value
            if best_ask < fair_value - threshold:
                best_ask_volume = order_depth.sell_orders[best_ask]
                max_buy_volume = min(position_limit - current_position, -best_ask_volume)
                if max_buy_volume > 0:
                    orders.append(Order(product, best_ask, max_buy_volume))
            
            # Sell logic: if best bid is significantly above fair value
            if best_bid > fair_value + threshold:
                best_bid_volume = order_depth.buy_orders[best_bid]
                max_sell_volume = min(position_limit + current_position, best_bid_volume)
                if max_sell_volume > 0:
                    orders.append(Order(product, best_bid, -max_sell_volume))
            
            result[product] = orders
        
        return result, 0, ""