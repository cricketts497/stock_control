# Stock control GUI project
Form to simplify database stock management with ebay orders

## Adding orders
Orders detailing are added manually, including date, postcode and order amount. Default values are set for the ebay, paypal, and postage and packaging costs.
Items are accessed via their unique `item_id` in the stock database, the current stock is checked to see if the order can be fulfilled.
When orders are committed, they are added to an orders.csv database and the stock is deducted from the stock.csv database. Multiple items can be included in each order, the form expands automatically as you add more items.
The last order can be removed using the undo button, this removes the order from the orders database and re-adds the stock.

![Order adding form](/images/order_form.png)

## Adding stock
Stock can be added on the second tab with the same `item_id` values. The form expands automatically as you add items. The last stock add can be undone with the undo button.

![Stock adding form](/images/stock_form.png)

## Installation and run instructions
1. Clone the repository into your working directory with `git clone https://github.com/cricketts497/stock_control`
2. Install python 3 and pip
3. `pip install PyQt5 pandas`
4. `python main.py`

## Edits
Filepaths and cost amounts can be edited in the class variables in MainWindow.py
