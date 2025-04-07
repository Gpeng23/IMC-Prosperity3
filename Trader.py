from datamodel import Order, OrderDepth, TradingState
from typing import Dict, List
from collections import deque
from datetime import datetime
import statistics

class Trader:
    def __init__(self, debug_mode: bool = True):
        """
        Initialize the Trader class with necessary variables and settings.
        - debug_mode: If True, print detailed logs for debugging and understanding.
        """
        self.debug_mode = debug_mode  # Controls whether we print logs or not

        # Configuration for SQUID_INK
        self.max_position = 50  # Maximum position limit in either direction (+50 or -50)
        self.short_window = 5   # Short-term moving average window (e.g., 5 periods)
        self.long_window = 20   # Long-term moving average window (e.g., 20 periods)
        self.deviation_threshold = 0.02  # 2% deviation from fair value to confirm buy/sell signals

        # Data storage for price history and moving averages
        self.price_history = deque(maxlen=self.long_window)  # Store mid-prices to calculate moving averages
        self.short_ma_history = deque(maxlen=self.long_window)  # Store short-term moving averages
        self.long_ma_history = deque(maxlen=self.long_window)   # Store long-term moving averages

        # Position and PnL tracking
        self.position = 0  # Current position in SQUID_INK (positive for long, negative for short)
        self.cost_basis = deque()  # FIFO queue of (price, qty) tuples to track cost basis for PnL
        self.realized_pnl = 0.0  # Realized profit/loss in SeaShells
        self.seashells_balance = 0.0  # Balance in SeaShells (not used directly but tracked for completeness)

    def log(self, message: str):
        """
        Log a message with a timestamp if debug_mode is True.
        - message: The string message to log.
        """
        if self.debug_mode:
            print(f"[{datetime.now()}] {message}")

    def calculate_mid_price(self, order_depth: OrderDepth) -> float:
        """
        Calculate the mid-price as the average of the best bid and best ask.
        This is our estimate of the current market price for SQUID_INK.
        - order_depth: The OrderDepth object containing buy_orders and sell_orders.
        Returns the mid-price as a float.
        """
        if not order_depth.buy_orders or not order_depth.sell_orders:
            self.log("No buy or sell orders available to calculate mid-price.")
            return None

        best_bid = max(order_depth.buy_orders.keys())  # Highest price someone is willing to buy at
        best_ask = min(order_depth.sell_orders.keys())  # Lowest price someone is willing to sell at
        mid_price = (best_bid + best_ask) / 2
        self.log(f"Mid-price calculated: Best Bid = {best_bid}, Best Ask = {best_ask}, Mid-Price = {mid_price:.2f}")
        return mid_price

    def update_moving_averages(self, mid_price: float):
        """
        Update the short-term and long-term moving averages with the latest mid-price.
        - mid_price: The current mid-price to add to the price history.
        """
        # Add the new mid-price to the price history
        self.price_history.append(mid_price)

        # Calculate short-term moving average (last 5 prices)
        if len(self.price_history) >= self.short_window:
            short_ma = statistics.mean(list(self.price_history)[-self.short_window:])
            self.short_ma_history.append(short_ma)
            self.log(f"Short-term MA (window={self.short_window}): {short_ma:.2f}")
        else:
            self.short_ma_history.append(mid_price)  # Use mid-price until we have enough data
            self.log(f"Short-term MA not yet available, using mid-price: {mid_price:.2f}")

        # Calculate long-term moving average (last 20 prices)
        if len(self.price_history) >= self.long_window:
            long_ma = statistics.mean(list(self.price_history))
            self.long_ma_history.append(long_ma)
            self.log(f"Long-term MA (window={self.long_window}): {long_ma:.2f}")
        else:
            self.long_ma_history.append(mid_price)  # Use mid-price until we have enough data
            self.log(f"Long-term MA not yet available, using mid-price: {mid_price:.2f}")

    def detect_signal(self, mid_price: float) -> str:
        """
        Detect trading signals based on moving average crossovers and price deviations.
        - mid_price: The current mid-price to compare against fair value.
        Returns a signal: "BUY", "SELL", or "HOLD".
        """
        # Need at least two periods of moving averages to detect a crossover
        if len(self.short_ma_history) < 2 or len(self.long_ma_history) < 2:
            self.log("Not enough MA data to detect signals. Holding position.")
            return "HOLD"

        # Get current and previous moving averages
        current_short_ma = self.short_ma_history[-1]
        previous_short_ma = self.short_ma_history[-2]
        current_long_ma = self.long_ma_history[-1]
        previous_long_ma = self.long_ma_history[-1]

        # Fair value is approximated as the current long-term MA (our estimate of the "true" price)
        fair_value = current_long_ma
        self.log(f"Fair Value (Long-term MA): {fair_value:.2f}")

        # Detect crossover for cyclical behavior
        # Buy signal: Short MA crosses above Long MA (trough), and price is below fair value
        # Sell signal: Short MA crosses below Long MA (peak), and price is above fair value
        if (previous_short_ma <= previous_long_ma and current_short_ma > current_long_ma):
            self.log("Inflection Point Detected: Short MA crossed above Long MA (Potential Trough).")
            # Confirm the buy signal with price deviation
            if mid_price < fair_value * (1 - self.deviation_threshold):
                self.log(f"BUY Signal: Price {mid_price:.2f} is {((fair_value - mid_price) / fair_value * 100):.2f}% below Fair Value {fair_value:.2f}")
                return "BUY"
            else:
                self.log(f"Price {mid_price:.2f} not sufficiently below Fair Value {fair_value:.2f}. Holding.")
                return "HOLD"

        elif (previous_short_ma >= previous_long_ma and current_short_ma < current_long_ma):
            self.log("Inflection Point Detected: Short MA crossed below Long MA (Potential Peak).")
            # Confirm the sell signal with price deviation
            if mid_price > fair_value * (1 + self.deviation_threshold):
                self.log(f"SELL Signal: Price {mid_price:.2f} is {((mid_price - fair_value) / fair_value * 100):.2f}% above Fair Value {fair_value:.2f}")
                return "SELL"
            else:
                self.log(f"Price {mid_price:.2f} not sufficiently above Fair Value {fair_value:.2f}. Holding.")
                return "HOLD"

        else:
            self.log("No MA crossover detected. Holding position.")
            return "HOLD"

    def simulate_execution(self, order_depth: OrderDepth, volume: int, is_buy: bool) -> tuple[float, int]:
        """
        Simulate executing a trade to calculate the average price and filled volume.
        - order_depth: The OrderDepth object containing buy_orders and sell_orders.
        - volume: The desired volume to trade (positive for buy, negative for sell).
        - is_buy: True if buying, False if selling.
        Returns a tuple of (average_price, filled_volume).
        """
        if is_buy:
            orders = sorted(order_depth.sell_orders.items())  # Sell orders for buying
            direction = 1
        else:
            orders = sorted(order_depth.buy_orders.items(), reverse=True)  # Buy orders for selling
            direction = -1

        total_cost = 0.0
        remaining = abs(volume)
        filled = 0

        for price, qty in orders:
            if remaining <= 0:
                break
            available = abs(qty)
            trade_qty = min(remaining, available)
            total_cost += price * trade_qty
            remaining -= trade_qty
            filled += trade_qty

        avg_price = total_cost / filled if filled > 0 else 0
        filled_volume = direction * filled
        self.log(f"Simulated Execution: {'BUY' if is_buy else 'SELL'} {abs(filled_volume)} @ {avg_price:.2f}")
        return avg_price, filled_volume

    def update_position_and_pnl(self, price: float, volume: int):
        """
        Update the position, cost basis, and realized PnL after a trade.
        - price: The price at which the trade was executed.
        - volume: The volume traded (positive for buy, negative for sell).
        """
        self.position += volume  # Update position
        self.log(f"Updated Position: {self.position}")

        if volume > 0:  # Buy trade
            self.cost_basis.append((price, volume))
            self.seashells_balance -= price * volume
            self.log(f"BUY: Added to cost basis - Price: {price:.2f}, Qty: {volume}")

        elif volume < 0:  # Sell trade
            volume_left = abs(volume)
            while volume_left > 0 and self.cost_basis:
                basis_price, basis_qty = self.cost_basis[0]
                qty_to_close = min(volume_left, basis_qty)
                profit = (price - basis_price) * qty_to_close
                self.realized_pnl += profit
                self.seashells_balance += price * qty_to_close
                volume_left -= qty_to_close
                if qty_to_close == basis_qty:
                    self.cost_basis.popleft()
                else:
                    self.cost_basis[0] = (basis_price, basis_qty - qty_to_close)
                self.log(f"SELL: Realized PnL += {profit:.2f}, New Realized PnL: {self.realized_pnl:.2f}")

    def calculate_unrealized_pnl(self, order_depth: OrderDepth) -> float:
        """
        Calculate the unrealized PnL based on the current market price.
        - order_depth: The OrderDepth object to get current market prices.
        Returns the unrealized PnL as a float.
        """
        if self.position == 0 or not order_depth.buy_orders or not order_depth.sell_orders:
            return 0.0

        best_bid = max(order_depth.buy_orders.keys())
        best_ask = min(order_depth.sell_orders.keys())
        mark_price = best_bid if self.position > 0 else best_ask  # Use bid if long, ask if short
        total_cost = sum(p * q for p, q in self.cost_basis)
        unrealized = self.position * (mark_price - total_cost / self.position) if self.position != 0 else 0.0
        self.log(f"Unrealized PnL: Mark Price = {mark_price:.2f}, Position = {self.position}, Unrealized PnL = {unrealized:.2f}")
        return unrealized

    def generate_orders(self, order_depth: OrderDepth, signal: str) -> List[Order]:
        """
        Generate buy or sell orders based on the trading signal.
        - order_depth: The OrderDepth object containing buy_orders and sell_orders.
        - signal: The trading signal ("BUY", "SELL", or "HOLD").
        Returns a list of Orders to execute.
        """
        orders = []

        # Base trade size (e.g., 10 units per trade)
        base_size = 10

        if signal == "BUY" and self.position < self.max_position:
            size = min(base_size, self.max_position - self.position)
            if size > 0:
                avg_price, filled = self.simulate_execution(order_depth, size, True)
                if filled > 0:
                    orders.append(Order("SQUID_INK", avg_price, filled))
                    self.update_position_and_pnl(avg_price, filled)
                    self.log(f"EXECUTED BUY: {filled} @ {avg_price:.2f}")

        elif signal == "SELL" and self.position > -self.max_position:
            size = min(base_size, self.max_position + self.position)
            if size > 0:
                avg_price, filled = self.simulate_execution(order_depth, -size, False)
                if filled < 0:
                    orders.append(Order("SQUID_INK", avg_price, filled))
                    self.update_position_and_pnl(avg_price, filled)
                    self.log(f"EXECUTED SELL: {abs(filled)} @ {avg_price:.2f}")

        else:
            self.log("No trade executed: Signal is HOLD or position limit reached.")

        return orders

    def print_summary(self, order_depth: OrderDepth):
        """
        Print a summary of the current state, including position and PnL.
        - order_depth: The OrderDepth object to calculate unrealized PnL.
        """
        unrealized = self.calculate_unrealized_pnl(order_depth)
        total_pnl = self.realized_pnl + unrealized
        self.log("\n=== Trading Summary ===")
        self.log(f"SQUID_INK: Position = {self.position}")
        self.log(f"Realized PnL = {self.realized_pnl:.2f} SeaShells")
        self.log(f"Unrealized PnL = {unrealized:.2f} SeaShells")
        self.log(f"Total PnL = {total_pnl:.2f} SeaShells\n")

    def run(self, state: TradingState) -> tuple[Dict[str, List[Order]], int, str]:
        """
        Main trading loop executed each tick.
        - state: The TradingState object containing order_depths, position, etc.
        Returns a tuple of (orders dictionary, conversions, custom string).
        """
        # Initialize the result dictionary for orders
        result = {"SQUID_INK": []}

        # Update position from the state
        self.position = state.position.get("SQUID_INK", 0)
        self.log(f"Starting Position: {self.position}")

        # Get the order depth for SQUID_INK
        if "SQUID_INK" not in state.order_depths:
            self.log("SQUID_INK not found in order depths. Skipping this tick.")
            return result, 0, ""

        order_depth = state.order_depths["SQUID_INK"]

        # Step 1: Calculate the mid-price
        mid_price = self.calculate_mid_price(order_depth)
        if mid_price is None:
            self.log("Cannot proceed without a valid mid-price. Skipping this tick.")
            return result, 0, ""

        # Step 2: Update moving averages
        self.update_moving_averages(mid_price)

        # Step 3: Detect trading signal
        signal = self.detect_signal(mid_price)
        self.log(f"Trading Signal: {signal}")

        # Step 4: Generate orders based on the signal
        orders = self.generate_orders(order_depth, signal)
        result["SQUID_INK"] = orders

        # Step 5: Print summary of position and PnL
        self.print_summary(order_depth)

        # No conversions since we're only trading SQUID_INK in SeaShells
        conversions = 0
        custom_string = ""

        return result, conversions, custom_string