from flask import Flask, jsonify, request
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import bcrypt
from marshmallow import fields, validate
from marshmallow import ValidationError
from datetime import datetime
from password import my_password

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://root:{my_password}@localhost/ecommerce_db'
db = SQLAlchemy(app)
ma = Marshmallow(app)

### Customer Model & Schema ###
class Customer(db.Model):
    __tablename__ = 'Customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(300), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)

    account = db.relationship('CustomerAccount', backref='customer')
    order = db.relationship('Order', backref='customer')

class CustomerSchema(ma.Schema):
    name = fields.String(required=True)
    email = fields.String(required=True)
    phone = fields.String(required=True)

    class Meta:
        fields = ('name', 'email', 'phone', 'id')

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)


### CustomerAccounts Model & Schema ###
class CustomerAccount(db.Model):
    __tablename__ = 'CustomerAccounts'
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id'))
    username = db.Column(db.String(75), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)

    customer = db.relationship('Customer', backref='customer_account', uselist=False, lazy=True)

class CustomerAccountSchema(ma.Schema):
    customer_id = fields.Integer(required=True)
    username = fields.String(required=True, validate=validate.Length(min=8))
    password = fields.String(required=True, validate=validate.Length(min=16))
    # TODO maybe add back load_only=True

account_schema = CustomerAccountSchema()

### Orders Model & Schema ###
class Order(db.Model):
    __tablename__ = 'Orders'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id'))
    order_date_time = db.Column(db.DateTime, default=datetime.now(datetime.UTC), nullable=False)
    total_amount = db.Column(db.Numeric(precision=20, scale=2), nullable=False)

    customer = db.relationship('Customer', backref='orders')


### OrderDetails Many-to-Many Association Table ###
order_details = db.Table('OrderDetails',
    db.Column('order_id', db.Integer, db.ForeignKey('Orders.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('Products.id'))
    )


### Products Model & Schema ###
class Product(db.Model):
    __tablename__ = 'Products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    catalog = db.relationship('Catalog', backref='product', cascade='all, delete-orphan', lazy=True)
    orders = db.relationship('Order', secondary=order_details, backref=db.backref('products', lazy='dynamic'))

    def deactivate(self):
        self.is_active = False
        db.session.commit()

class ProductSchema(ma.Schema):
    name = fields.String(required=True, validate=validate.Length(min=1))
    price = fields.Float(required=True, validate=validate.Range(min=0))

    class Meta:
        fields = ('name', 'price', 'is_active', 'id')

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

###TODO Posibly adjust this to be included within Product class/model/schema
### Catalog Model & Schema ###
class Catalog(db.Model):
    __tablename__ = 'Catalog'
    product_id = db.Column(db.Integer, db.ForeignKey('Products.id'), nullable=False)
    product_stock = db.Column(db.Integer, nullable=False, default=0)

    product = db.relationship('Product', backref=db.backref('catalog_entries'))

    def deactivate_product(self):
        self.product_stock = 0
        db.session.commit()

class CatalogSchema(ma.Schema):
    product_id = fields.Integer(required=True)
    product_stock = fields.Integer(required=True)
    product_name = fields.Method('get_product_name')

    def get_product_name(self, obj):
        return obj.product.name if obj.product else None

    class Meta:
        load_instance = True

catalog_schema = CatalogSchema()
catalogs_schema = CatalogSchema(many=True)


### Customer Endpoints & Methods ###
@app.route('/customers', methods=['POST'])
def add_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as ve:
        return jsonify(ve.messages), 400
    
    new_customer = Customer(
        name = customer_data['name'],
        email = customer_data['email'],
        phone = customer_data['phone']
    )

    db.session.add(new_customer)
    db.session.commit()
    return jsonify({"message": "New customer added successfully"}), 201

@app.route('/customers', methods=['GET'])
def get_customers():
    customers = Customer.query.all()
    return customers_schema.jsonify(customers)

@app.route('/customers/specified-id', methods=['GET'])
def get_customer_by_id():
    id = request.args.get('id')
    customer = Customer.query.filter_by(id = id).first()
    if customer:
        return customer_schema.jsonify(customer)
    else:
        return jsonify({"message": "Customer not found"}), 404

@app.route('/customers/<int:id>', methods=['PUT'])
def update_customer(id):
    customer = Customer.query.get_or_404(id)
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as ve:
        return jsonify(ve.messages), 400

    customer.name = customer_data.get('name', customer.name)
    customer.email = customer_data.get('email', customer.email)
    customer.phone = customer_data.get('phone', customer.phone)
    db.session.commit()
    return jsonify({"message": "Customer details updated successfully"}), 200

@app.route('/customers/<int:id>', methods=['DELETE'])
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "Customer removed successfully"}), 200


### CustomerAccount Endpoints & Methods ###
@app.route('/accounts', methods=['POST'])
def create_customer_account():
    try:
        account_data = account_schema.load(request.json)
    except ValidationError as ve:
        return jsonify(ve.messages), 400
    
    # Hashing password indluding a salt for added security
    customer_password = account_data['password']
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(customer_password, salt)
    new_account = CustomerAccount(customer_id = account_data['customer_id'],
                                  username = account_data['username'],
                                  password = hashed_password
                                  )
    
    db.session.add(new_account)
    db.session.commit()
    return jsonify({"message": "New customer account added successfully"}), 201

@app.route('/accounts/specified-customer', methods=['GET'])
def get_account_details_by_customer_id():
    customer_id = request.args.get('customer_id')
    account = CustomerAccount.query.filter_by(customer_id = customer_id).first_or_404()
    return account_schema.jsonify(account)

@app.route('/accounts/specified-customer', methods=['PUT'])
def update_customer_account():
    customer_id = request.args.get('customer_id')
    account = CustomerAccount.query.get_or_404(customer_id)
    try:
        account_data = account_schema.load(request.json)
    except ValidationError as ve:
        return jsonify(ve.messages), 400
    
    # Hashing password indluding a salt for added security
    new_password = account_data['password']
    salt = bcrypt.gensalt()
    new_hashed_password = bcrypt.hashpw(new_password, salt)
    account.customer_id = customer_id
    account.username = account_data.get('username', account.username)
    account.password = new_hashed_password
    db.session.commit()
    return jsonify({"message": "Customer account updated successfully"}), 200

@app.route('/accounts/specified-customer', methods=['DELETE'])
def delete_customer_account():
    customer_id = request.args.get('customer_id')
    account = CustomerAccount.query.get_or_404(customer_id)
    db.session.delete(account)
    db.session.commit()
    return jsonify({"message": "Account removed successfully"}), 200


### Product Endpoints & Methods ###
@app.route('/products', methods=['POST'])
def add_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as ve:
        return jsonify(ve.messages), 400
    
    new_product = Product(name = product_data['name'],
                          price = product_data['price'],
                          )
    db.session.add(new_product)
    db.session.commit()

    # Create a Catalog Entry with new product info
    new_catalog_entry = Catalog(product_id = new_product.id)
    db.session.add(new_catalog_entry)
    db.session.commit()

    return jsonify({"message": "New product added and catalog entry created successfully"}), 201

@app.route('/products/<int:id>', methods=['GET'])
def get_product_by_id(id):
    product = Product.query.get_or_404(id)
    if product:
        return product_schema.jsonify(product)
    
@app.route('/products/active-products', methods=['GET'])
def get_active_products_details():
    active_products = Product.query.filter(Product.is_active == True).all()
    if active_products:
        return products_schema.jsonify(active_products)
    else:
        return jsonify({"message": "No products available"}), 404

@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as ve:
        return jsonify(ve.messages), 400
    
    product.name = product_data.get('name', product.name)
    product.price = product_data.get('price', product.price)
    product.is_active = product_data.get('is_active', product.is_active)
    db.session.commit()

    # If the product is_active=False update Catalog stock amount to 0
    catalog_entry = Catalog.query.filter_by(product_id=id).first()
    if catalog_entry and not product.is_active:
        catalog_entry.deactivate_product()

    return jsonify({"message": "Product updated successfully"}), 200

@app.route('/products/specified-product', methods=['PUT'])
def soft_delete_product():
    id = request.args.get('id')
    product = Product.query.get_or_404(id)
    product.deactivate()
    catalog_entry = Catalog.query.filter_by(product_id = id).first()
    if catalog_entry:
        catalog_entry.deactivate_product()

    return jsonify({"message": "Successfully deactivated product from catalog"}), 200


### Catalog Endpoints & Methods ###
@app.route('/catalog', methods=['POST'])
def add_product_to_catalog():
    try:
        catalog_data = catalog_schema.load(request.json)
    except ValidationError as ve:
        return jsonify(ve.messages), 400
    
    new_catalog_entry = Catalog(product_id = catalog_data['product_id'])
    db.session.add(new_catalog_entry)
    db.session.commit()

    return jsonify({"message": "New catalog entry created successfully"}), 201

@app.route('/catalog/active-products', methods=['GET'])
def get_active_catalog_products():
    active_catalog = Catalog.query.filter(Product.is_active == True).all()
    if active_catalog:
        return catalogs_schema.jsonify(active_catalog)
    else:
        return jsonify({"message": "No active products"}), 404
    
@app.route('/catalog', methods=['GET'])
def get_full_catalog():
    full_catalog = Catalog.query.all()
    return catalogs_schema.jsonify(full_catalog)

@app.route('/catalog/check_stock', methods=['GET'])
def monitor_stock_levels():
    stock_threshold = 10
    low_stock_products = Catalog.query.filter(1 < Catalog.product_stock < stock_threshold).all()
    if low_stock_products:
        print("* Products Below Stock Threshold: *")
        for product in low_stock_products:
            print(f"Product: {product.product_name}\n\t~ Product ID: {product.product_id}\n\t- Stock: {product.product_stock}")
            # TODO add restock trigger w/datetime ordered and auto-update stock for products on specified date/timeframe

@app.route('/catalog/update-stock/specified-product')
def update_stock_by_product_id():
    product_id = request.args.get('product_id')
    catalog_entry = Catalog.query.filter_by(product_id = product_id).first_or_404()
    try:
        catalog_data = catalog_schema.load(request.json)
    except ValidationError as ve:
        return jsonify(ve.messages), 400
    
    catalog_entry.product_id = product_id
    catalog_entry.product_stock = catalog_data['product_stock']
    db.session.commit()

    return jsonify({"message": "Successfully updated stock for product in catalog"}), 200


### Order Endpoints & Methods ###
# TODO Place order
# @app.route('/orders')
# def add_order():


# TODO Retrieve order & details by ID
# @app.route()

# TODO Track order status & progress. Order dates, expected delivery dates
# @app.route()


# TODO BONUS retrieve order history for customer


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)