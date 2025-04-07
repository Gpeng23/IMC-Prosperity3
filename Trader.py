from datamodel import Order, OrderDepth, TradingState, Listing
from typing import List, Dict, Optional
from collections import deque, defaultdict
from datetime import datetime
import statistics

class Trader:
    def __init__(self, debug_mode: bool = True):
        self.debug_mode = debug_mode

        # Define key parameters for each product (position limits, fair value thresholds, etc.)
        self.product_config = {
            "RAINFOREST_RESIN": {"limit": 50, "threshold": 1.5, "window": 10, "volume_weight": 0.7, "arb_threshold": 0.02},
            "KELP": {"limit": 50, "threshold": 1.2, "window": 8, "volume_weight": 0.6, "arb_threshold": 0.015},
            "SQUID_INK": {"limit": 50, "threshold": 2.0, "window": 5, "volume_weight": 0.8, "arb_threshold": 0.025},
            "PIZZA": {"limit": 50, "threshold": 1.5, "window": 10, "volume_weight": 0.7, "arb_threshold": 0.02},
            "SNOWBALL": {"limit": 50, "threshold": 1.5, "window": 10, "volume_weight": 0.7, "arb_threshold": 0.02}
        }

        # Historical price window for each product for fair value estimation
        self.price_history = {p: deque(maxlen=c["window"]) for p, c in self.product_config.items()}
        
        # FIFO cost tracking to calculate realized PnL
        self.cost_basis = {p: deque() for p in self.product_config}

        # Tracks profits from closed positions
        self.realized_pnl = {p: 0.0 for p in self.product_config}
        
        # Cash balance in Seashells (used to simulate PnL)
        self.seashells_balance = 0.0

        # Not used in logic, reserved for future expansion/logging
        self.trade_log = []

        # Static conversion rates between in-game currencies
        self.conversion_matrix = {
            "Snowball": {"Snowball": 1.0, "Pizza": 1.45, "Silicon Nugget": 0.52, "SeaShell": 0.72},
            "Pizza": {"Snowball": 0.7, "Pizza": 1.0, "Silicon Nugget": 0.31, "SeaShell": 0.48},
            "Silicon Nugget": {"Snowball": 1.95, "Pizza": 3.1, "Silicon Nugget": 1.0, "SeaShell": 1.49},
            "SeaShell": {"Snowball": 1.34, "Pizza": 1.98, "Silicon Nugget": 0.64, "SeaShell": 1.0}
        }

        # Legacy pairwise conversion dictionary
        self.conversion_rates = {
            ("SNOWBALL", "PIZZA"): 1.45,
            ("PIZZA", "SNOWBALL"): 0.7
        }

    def log(self, message: str):
        # Utility function for debug output
        if self.debug_mode:
            print(f"[{datetime.now()}] {message}")

    def log_currency_trade_opportunity(self, state: TradingState):
        # This method checks if cross-currency arbitrage is possible by simulating trades through multiple currencies
        currencies = ["Snowball", "Pizza", "Silicon Nugget", "SeaShell"]
        products = [p for p in state.order_depths.keys() if p not in ["PIZZA", "SNOWBALL"]]  # Don't treat currencies as products

        for product in products:
            order_depth = state.order_depths[product]
            if not order_depth.buy_orders or not order_depth.sell_orders:
                continue

            best_bid = max(order_depth.buy_orders.keys())
            best_ask = min(order_depth.sell_orders.keys())

            for source_curr in currencies:
                for buy_curr in currencies:
                    if source_curr == buy_curr:
                        continue
                    for sell_curr in currencies:
                        if buy_curr == sell_curr or source_curr == sell_curr:
                            continue

                        conv_to_buy = self.conversion_matrix[source_curr][buy_curr]
                        if conv_to_buy == 0:
                            continue
                        cost_in_source_curr = best_ask / conv_to_buy

                        revenue_in_sell_curr = best_bid
                        conv_to_source = self.conversion_matrix[sell_curr][source_curr]
                        if conv_to_source == 0:
                            continue
                        revenue_in_source_curr = revenue_in_sell_curr * conv_to_source

                        edge = (revenue_in_source_curr - cost_in_source_curr) / cost_in_source_curr * 100
                        if edge > 1.0:
                            steps = (f"Buy {product} in {buy_curr} @ {best_ask}, "
                                    f"Convert {source_curr}→{buy_curr} @ {conv_to_buy:.2f}, "
                                    f"Sell in {sell_curr} @ {best_bid}, "
                                    f"Convert {sell_curr}→{source_curr} @ {conv_to_source:.2f}")
                            self.log(f"MANUAL TRADE OPPORTUNITY: {source_curr} → {buy_curr} → {product} → "
                                     f"{sell_curr} → {source_curr}: +{edge:.2f}% | Steps: {steps}")
