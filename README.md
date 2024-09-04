# E-Commerce-API
 Coding Temple Module 6 Mini-Project

## Overview
This is a Flask-based E-Commerce API that provides a comprehensive set of features for managing customers, products, and orders. The application integrates with a MySQL database using Flask-SQLAlchemy and Marshmallow for data modeling and validation.

## Key Features
1. **Customer and CustomerAccount Management**
   - Implemented CRUD (Create, Read, Update, Delete) endpoints for managing customers and their associated accounts.
   - Capture essential customer information, including name, email, and phone number.
   - Securely stores and manages customer account details, including username and password.

2. **Product Catalog Management**
   - Implemented CRUD endpoints for managing products in the e-commerce catalog.
   - Captures product details such as name and price.
   - Provides functionality to list all available products.
   - *Bonus features:*
     - View and manage product stock levels.
     - Automatically restocks products when stock levels fall below a specified threshold.

3. **Order Processing**
   - Implemented endpoints for customers to place new orders, specifying the products and quantities.
   - Captures essential order details, including order date and associated customer.
   - Allows customers to retrieve order details and track the status of their orders.
   - *Bonus features:*
     - Provides customers access to their order history.
     - Calculates the total price of each order based on the associated product prices.

4. **Database Integration**
   - Utilizes Flask-SQLAlchemy to integrate a MySQL database into the application.
   - Creates the necessary database models to represent customers, orders, products, and customer accounts.
   - Established proper relationships between the database tables.

5. **Data Validation and Error Handling**
   - Implemented data validation mechanisms to ensure user inputs meet specified criteria.
   - Implemented try & except blocks to handle errors gracefully and provide informative error messages.

6. **User Interface (Postman)**
   - Postman collections to organize and group API requests by functionality.
   - Separate collections for Customer Management, Product Management, Order Management, and Bonus Features.

## Getting Started

### Prerequisites
- Python 3.x
- MySQL Community Server
- MySQL Workbench
- Python dependencies:
  - Flask
  - Flask-SQLAlchemy
  - Flask-Marshmallow
  - Flask-Bcrypt
  - mysql-connector-python

## Installation:
*** **GitHub Repository** ***

[E-Commerce API Module6-MiniProject Repository](https://github.com/Tmiseray/E-Commerce-API)

*** **Cloning Option** ***
* If you have Git Bash installed, you can clone the repository using the URL
1. Create a 'Clone' Folder
2. Within the folder, right-click for Git Bash
3. From the GitHub Repository, click on the '<> Code' button and copy the link provided
4. Paste the link into your Git Bash and click 'Enter'
* If you have GitHub Desktop, when you click on the '<> Code' button you will have an option to 'Open with GitHub Desktop'
* If you have Visual Studio Code, when you click on the '<> Code' button you will have an option to 'Open with Visual Studio'
* [HTTPS] (https://github.com/Tmiseray/E-Commerce-API.git)
* [SSH] (git@github.com:Tmiseray/E-Commerce-API.git)
* [GitHubCLI] (`gh repo clone Tmiseray/E-Commerce-API`)

*** **Download Option** ***
1. From the GitHub Repository, click on the '<> Code' button
2. Click on 'Download Zip'
3. Extract contents of Zip file

*** **Update File & Run App** ***
1. Update the database connection details in the `app.py` & `password.py` files:
   - Locate the line `app.config['SQLALCHEMY_DATABASE_URI']` and replace the placeholder values with your MySQL connection details.
   - Locate the `password.py` file and replace the placeholder with your password
2. Start the Flask application:
   ```
   python app.py
   ```
3. Access the API endpoints using a tool like Postman. The Postman collections are available in the GitHub repository.

## API Endpoints

The E-Commerce API provides the following endpoints:

### Customer and CustomerAccount Management
- `POST /customers`: Create a new customer
- `GET /customers`: Retrieve all customers
- `GET /customers/specified-id`: Retrieve a customer by ID
- `PUT /customers/<int:id>`: Update a customer's details
- `DELETE /customers/<int:id>`: Delete a customer
- `POST /accounts`: Create a new customer account
- `GET /accounts/specified-customer`: Retrieve a customer account by customer ID
- `PUT /accounts/specified-customer`: Update a customer account
- `DELETE /accounts/specified-customer`: Delete a customer account

### Product Catalog Management
- `POST /products`: Create a new product
- `GET /products/<int:id>`: Retrieve a product by ID
- `GET /products/active-products`: Retrieve all active products
- `PUT /products/<int:id>`: Update a product's details
- `PUT /products/specified-product`: Soft-delete a product (deactivate)
- `POST /catalog`: Add a new product to the catalog
- `GET /catalog/active-products`: Retrieve all active products in the catalog
- `GET /catalog`: Retrieve the full catalog
- `POST /catalog/stock-monitor`: Monitor and restock low-stock products
- `POST /catalog/update-stock/specified-product`: Update the stock level for a specific product

### Order Processing
- `POST /place-order`: Place a new order
- `GET /orders/<int:id>`: Retrieve an order by ID
- `POST /orders/track-status`: Track the status of an order
- `POST /orders/history-for-customer`: Retrieve the order history for a customer

## Bonus Features
The E-Commerce API includes the following bonus features:

1. **View and Manage Product Stock Levels**
   - Implement endpoints to view and update the stock levels for each product in the catalog.

2. **Automatically Restock Products When Low**
   - Develop an endpoint that monitors product stock levels and triggers restocking when they fall below a specified threshold.

3. **Manage Order History**
   - Create an endpoint that allows customers to access their order history, listing all previous orders placed.

4. **Calculate Order Total Price**
   - Include an endpoint that calculates the total price of items in a specific order, considering the prices of the products included in the order.

## Contributing
Contributions to the E-Commerce API project are welcome! If you encounter any issues or have suggestions for improvements, please feel free to open a new issue or submit a pull request.
