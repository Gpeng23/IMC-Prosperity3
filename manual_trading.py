# Define the conversion rates from the table
conversion_rates = {
    "Snowballs": {"Snowballs": 1.0, "Pizzas": 1.45, "Silicon Nuggets": 0.52, "SeaShells": 0.72},
    "Pizzas": {"Snowballs": 0.7, "Pizzas": 1.0, "Silicon Nuggets": 0.31, "SeaShells": 0.48},
    "Silicon Nuggets": {"Snowballs": 1.95, "Pizzas": 3.1, "Silicon Nuggets": 1.0, "SeaShells": 1.49},
    "SeaShells": {"Snowballs": 1.34, "Pizzas": 1.98, "Silicon Nuggets": 0.64, "SeaShells": 1.0}
}

# List of currencies (excluding SeaShells for intermediate steps, but including it for conversions)
currencies = ["Snowballs", "Pizzas", "Silicon Nuggets", "SeaShells"]
intermediate_currencies = ["Snowballs", "Pizzas", "Silicon Nuggets"]  # Exclude SeaShells for intermediate steps

# Track if we find any profitable paths
profitable = False
print("Analyzing all possible conversion paths starting and ending with SeaShells...\n")

# Start with 1 SeaShell
initial_amount = 1.0

# Five nested loops to explore paths of up to 5 conversions
for curr1 in intermediate_currencies:
    # Step 1: SeaShells -> curr1
    rate1 = conversion_rates["SeaShells"][curr1]
    amount1 = initial_amount * rate1

    for curr2 in intermediate_currencies:
        # Step 2: curr1 -> curr2
        rate2 = conversion_rates[curr1][curr2]
        amount2 = amount1 * rate2

        for curr3 in intermediate_currencies:
            # Step 3: curr2 -> curr3
            rate3 = conversion_rates[curr2][curr3]
            amount3 = amount2 * rate3

            for curr4 in intermediate_currencies:
                # Step 4: curr3 -> curr4
                rate4 = conversion_rates[curr3][curr4]
                amount4 = amount3 * rate4

                # Step 5: curr4 -> SeaShells
                rate5 = conversion_rates[curr4]["SeaShells"]
                final_amount = amount4 * rate5

                # Calculate profit and edge
                profit = final_amount - initial_amount
                edge = (final_amount - initial_amount) / initial_amount * 100

                # Construct the path
                path = f"SeaShells -> {curr1} -> {curr2} -> {curr3} -> {curr4} -> SeaShells"

                # Check if the path is profitable
                if final_amount > initial_amount:
                    profitable = True
                    print(f"Profitable Path: {path}")
                    print(f"  Start: {initial_amount:.4f} SeaShells, End: {final_amount:.4f} SeaShells")
                    print(f"  Profit: {profit:.4f} SeaShells, Edge: {edge:.2f}%\n")
                else:
                    print(f"Non-profitable Path: {path}")
                    print(f"  Start: {initial_amount:.4f} SeaShells, End: {final_amount:.4f} SeaShells")
                    print(f"  Loss: {profit:.4f} SeaShells, Edge: {edge:.2f}%\n")

# Summary
if profitable:
    print("Yes, manual trading can be profitable starting and ending with SeaShells!")
else:
    print("No profitable paths found starting and ending with SeaShells.")