# Stock control GUI project
Form to simplify database stock management with ebay orders

## Adding orders
Orders detailing are added manually, including date, postcode and order amount. Default values are set for the ebay, paypal, and postage and packaging costs.
Items are accessed via their unique `item_id` in the stock database, the current stock is checked to see if the order can be fulfilled.
When orders are committed, they are added to an orders.csv database and the stock is deducted from the stock.csv database.

## Adding stock
Stock can be added on the second tab with the same `item_id` values.
