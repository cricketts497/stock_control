# Stock control GUI project
Form to simplify database stock management with ebay orders.

## Searching for items
Items can be found in the stock database using the search field, by their id, manufacturer, category or description. Search terms can be separated by a space; any fields containing any of the terms are returned into the table. Items with low stock (Hard coded as 15 in `searchTable.LOW_STOCK_LIMIT`) can be returned with the button. The returned table data can be saved to csv.

![Searching table](/images/search_form.png)

## Adding orders
Orders detailing are added manually, including date, postcode and order amount. Default values are set for the ebay, paypal, and postage and packaging costs.
Items are accessed via their unique `item_id` in the stock database (these are case insensitive, characters are capitalised in the database), the current stock is checked to see if the order can be fulfilled.
When orders are committed, they are added to an orders.csv database and the stock is deducted from the stock.csv database. Multiple items can be included in each order, the form expands automatically as you add more items.
The last order can be removed using the undo button, this removes the order from the orders database and re-adds the stock.

![Order adding form](/images/order_form.png)

## Adding stock
Stock can be added on the second tab with the same `item_id` values. The form expands automatically as you add items. When the stock add is commited, the stock is added to the stock.csv database and the details are added to stock_adding.csv. The last stock add can be undone with the undo button.

![Stock adding form](/images/stock_form.png)

## Installation and run instructions
1. Clone the repository into your working directory with `git clone https://github.com/cricketts497/stock_control`
2. Install python 3 and pip
3. `pip install PyQt5 pandas google-api-python-client google-auth-oauthlib`
4. Create/ get OAuth 2.0 Client IDs for google drive access for the application (https://console.developers.google.com/apis/credentials), save them in `../client_secret.json` relative to your working directory
5. `python main.py`

## Edits
Filepaths and cost amounts can be edited in the class variables in MainWindow.py, the location of the google drive api credentials can be edited in driveAccess.py (`DriveAccess.CREDENTIALS`)
