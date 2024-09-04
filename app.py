from flask import Flask, jsonify, request
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import bcrypt
from marshmallow import fields, validate
from marshmallow import ValidationError
from datetime import datetime, date, timezone, timedelta
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

    account = db.relationship('CustomerAccount', back_populates='linked_customer', uselist=False)
    order = db.relationship('Order', back_populates='customer', overlaps='customer_order')

class CustomerSchema(ma.Schema):
    name = fields.String(required=True)
    email = fields.String(required=True)
    phone = fields.String(required=True)

    class Meta:
        fields = ('name', 'email', 'phone', 'id')

class UpdateCustomerSchema(ma.Schema):
    name = fields.String(required=False)
    email = fields.String(required=False)
    phone = fields.String(required=False)

    class Meta:
        fields = ('name', 'email', 'phone', 'id')

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)
update_customer_schema = UpdateCustomerSchema()

### CustomerAccounts Model & Schema ###
class CustomerAccount(db.Model):
    __tablename__ = 'CustomerAccounts'
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id'), primary_key=True)
    username = db.Column(db.String(75), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)

    linked_customer = db.relationship('Customer', back_populates='account')

class AccountSchema(ma.Schema):
    customer_id = fields.Integer(required=True)
    username = fields.String(required=True, validate=validate.Length(min=8))
    password = fields.String(required=True, validate=validate.Length(min=16))

# Schema specifically for account updates
class UpdateAccountSchema(ma.Schema):
    customer_id = fields.Integer(required=False)
    username = fields.String(required=False, validate=validate.Length(min=8))
    password = fields.String(required=False, validate=validate.Length(min=16))

update_account_schema = UpdateAccountSchema()
account_schema = AccountSchema()

### OrderDetails Model & Schema ###
class OrderDetail(db.Model):
    __tablename__ = 'OrderDetails'
    order_id = db.Column(db.Integer, db.ForeignKey('Orders.id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('Products.id'), primary_key=True)
    product_name = db.Column(db.String, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_per_unit = db.Column(db.Numeric(precision=10, scale=2), nullable=False)

    order = db.relationship('Order', back_populates='order_details')
    product = db.relationship('Product', back_populates='order_details', primaryjoin='OrderDetail.product_id == Product.id')

class OrderDetailSchema(ma.Schema):
    order_id = fields.Integer(required=False)
    product_id = fields.Integer(required=False)
    product_name = fields.String(required=False)
    quantity = fields.Integer(required=True)
    price_per_unit = fields.Float(required=False)

    class Meta:
        fields = ('order_id', 'product_id', 'product_name', 'quantity', 'price_per_unit')

order_detail_schema = OrderDetailSchema()
order_details_schema = OrderDetailSchema(many=True)


### Orders Model & Schema ###
class Order(db.Model):
    __tablename__ = 'Orders'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id'), nullable=False)
    order_date_time = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    expected_delivery_date = db.Column(db.Date, nullable=False)
    total_amount = db.Column(db.Numeric(precision=10, scale=2), nullable=False)

    customer = db.relationship('Customer', back_populates='order', overlaps='order')
    order_details = db.relationship('OrderDetail', back_populates='order')

    def __init__(self, customer_id, total_amount, order_date_time=None):
        self.customer_id = customer_id
        self.total_amount = total_amount
        self.order_date_time = order_date_time if order_date_time else datetime.now(timezone.utc)
        self.expected_delivery_date = self.calculate_expected_delivary_date()

    def calculate_expected_delivary_date(self):
        return (self.order_date_time + timedelta(days=5)).date()

class OrderSchema(ma.Schema):
    customer_id = fields.Integer(required=True)
    order_date_time = fields.DateTime(dump_only=True)
    expected_delivery_date = fields.Date(dump_only=True)
    total_amount = fields.Float(dump_only=True)
    order_details = fields.List(fields.Nested(OrderDetailSchema), required=True)

    class Meta:
        load_instance = True
        fields = ('customer_id', 'order_date_time', 'expected_delivery_date', 'total_amount', 'order_details')

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)


### Products Model & Schema ###
class Product(db.Model):
    __tablename__ = 'Products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    catalog_entries = db.relationship('Catalog', back_populates='associated_product', overlaps='catalog')
    order_details = db.relationship('OrderDetail', back_populates='product', primaryjoin='Product.id == OrderDetail.product_id')

    def deactivate(self):
        self.is_active = False
        db.session.commit()

class ProductSchema(ma.Schema):
    name = fields.String(required=True, validate=validate.Length(min=1))
    price = fields.Float(required=True, validate=validate.Range(min=0))
    is_active = fields.Boolean(dump_only=True)

    class Meta:
        fields = ('name', 'price', 'is_active', 'id')

class UpdateProductSchema(ma.Schema):
    name = fields.String(required=False, validate=validate.Length(min=1))
    price = fields.Float(required=False, validate=validate.Range(min=0))
    is_active = fields.Boolean(required=False)

    class Meta:
        fields = ('name', 'price', 'is_active', 'id')

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)
update_product_schema = UpdateProductSchema()


### Catalog Model & Schema ###
class Catalog(db.Model):
    __tablename__ = 'Catalog'
    product_id = db.Column(db.Integer, db.ForeignKey('Products.id'), nullable=False, primary_key=True)
    product_stock = db.Column(db.Integer, nullable=False, default=0)
    last_restock_date = db.Column(db.DateTime, nullable=True)

    associated_product = db.relationship('Product', back_populates='catalog_entries', overlaps='catalog_entries')

    def deactivate_product(self):
        self.product_stock = 0
        self.associated_product.is_active = False
        db.session.commit()

class CatalogSchema(ma.Schema):
    product_id = fields.Integer(required=True)
    product_stock = fields.Integer(required=True)

    class Meta:
        load_instance = True

class UpdateCatalogSchema(ma.Schema):
    product_id = fields.Integer(required=False)
    product_stock = fields.Integer(required=True)

catalog_schema = CatalogSchema()
catalogs_schema = CatalogSchema(many=True)
update_catalog_schema = UpdateCatalogSchema()

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
        customer_data = update_customer_schema.load(request.json)
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
    
    # Hashing password including a salt for added security
    customer_password = account_data['password']
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(customer_password.encode('utf-8'), salt)
    new_account = CustomerAccount(
        customer_id = account_data['customer_id'],
        username = account_data['username'],
        password = hashed_password
        )
    
    db.session.add(new_account)
    db.session.commit()
    return jsonify({"message": "New customer account added successfully"}), 201

@app.route('/accounts/specified-customer', methods=['GET'])
def get_account_details_by_customer_id():
    customer_id = request.args.get('customer_id')
    account = CustomerAccount.query.filter_by(customer_id = customer_id).first()
    if account:
        return account_schema.jsonify(account)
    else:
        return jsonify({"error": "Account does not exist"}), 404

@app.route('/accounts/specified-customer', methods=['PUT'])
def update_customer_account():
    customer_id = request.args.get('customer_id')
    account = CustomerAccount.query.get_or_404(customer_id)
    try:
        account_data = update_account_schema.load(request.json)
    except ValidationError as ve:
        return jsonify(ve.messages), 400
    
    if 'username' in account_data:
        account.username = account_data['username']
    if 'password' in account_data:
        # Hashing password including a salt for added security
        new_password = account_data['password']
        salt = bcrypt.gensalt()
        new_hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), salt)
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
        product_data = update_product_schema.load(request.json)
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
    
    # Verify if product_id already exists in catalog
    product_id = catalog_data.get('product_id')
    product = Catalog.query.filter_by(product_id=product_id).first()
    if product:
        return jsonify({"error": f"Product ID: {product_id} already exists in catalog"}), 400
    
    # Set default product_stock if not provided
    product_stock = catalog_data.get('product_stock', 0)
    new_catalog_entry = Catalog(
        product_id = product_id,
        product_stock = product_stock
        )
    db.session.add(new_catalog_entry)
    db.session.commit()

    return jsonify({"message": "New catalog entry created successfully"}), 201

@app.route('/catalog/active-products', methods=['GET'])
def get_active_catalog_products():
    active_catalog = Catalog.query.join(Catalog.associated_product).filter(Product.is_active == True).all()
    if active_catalog:
        return catalogs_schema.jsonify(active_catalog)
    else:
        return jsonify({"message": "No active products"}), 404
    
@app.route('/catalog', methods=['GET'])
def get_full_catalog():
    full_catalog = Catalog.query.all()
    return catalogs_schema.jsonify(full_catalog)

@app.route('/catalog/stock-monitor', methods=['POST'])
def monitor_stock_levels():
    stock_threshold = 10
    restock_days_threshold = 7
    low_stock_products = Catalog.query.filter(Catalog.product_stock.between(1, stock_threshold-1)).all()

    response_data = {
        "message": None,
        "Products Below Threshold": [],
        "Restocking Details": []
    }

    if low_stock_products:
        response_data['message'] = "Stock levels checked and restocked where necessary"
        for catalog_entry in low_stock_products:
            product = Product.query.filter_by(id = catalog_entry.product_id).first()
            product_data = {
                "product_name": product.name,
                "product_id": catalog_entry.product_id,
                "product_stock": catalog_entry.product_stock
            }
            response_data['Products Below Threshold'].append(product_data)

            # Check last restock date
            if catalog_entry.last_restock_date:
                days_since_last_restock = (datetime.now(timezone.utc) - catalog_entry.last_restock_date).days
            else:
                # Force restock
                days_since_last_restock = restock_days_threshold + 1

            # Trigger restock if required
            if days_since_last_restock > restock_days_threshold:
                restock_quantity = 20
                catalog_entry.product_stock += restock_quantity
                catalog_entry.last_restock_date = datetime.now(timezone.utc)
                db.session.commit()
                restock_data = {
                    "product_id": catalog_entry.product_id,
                    "new_stock_quantity": catalog_entry.product_stock
                }
                response_data['Restocking Details'].append(restock_data)
    else:
        response_data['message'] = f"No products below stock threshold: {stock_threshold}"
        
    return jsonify(response_data), 201 if response_data['message'] == "Stock levels checked and restocked where necessary" else 404
            
@app.route('/catalog/update-stock/specified-product', methods=['POST'])
def update_stock_by_product_id():
    product_id = request.args.get('product_id')
    catalog_entry = Catalog.query.filter_by(product_id = product_id).first_or_404()
    try:
        catalog_data = update_catalog_schema.load(request.json)
    except ValidationError as ve:
        return jsonify(ve.messages), 400
    
    catalog_entry.product_id = product_id
    catalog_entry.product_stock = catalog_data['product_stock']
    db.session.commit()

    return jsonify({"message": f"Successfully updated stock in catalog for Product ID: {product_id}, New Stock Level: {catalog_entry.product_stock}"}), 200


### Order Endpoints & Methods ###
@app.route('/place-order', methods=['POST'])
def place_order():
    try:
        order_data = order_schema.load(request.json)
        # order_items = order_data.get('order_details', [])

        # Validate order details manually
        # validated_order_items = []
        # for item in order_items:
        #     if 'product_id' not in item and 'product_name' not in item:
        #         return jsonify({"error": "Either product_id or product_name must be provided for each item"}), 400
        #     if 'quantity' not in item:
        #         return jsonify({"error": "Quantity is required for each item"}), 400
        #     validated_order_items.append(item)

        # order_data['order_details'] = validated_order_items
        # order_data = order_schema.load(order_data)
    except ValidationError as ve:
        return jsonify(ve.messages), 400
    
    customer_id = order_data.get('customer_id')
    order_items = order_data.get('order_details', [])
    
    if not customer_id or not order_items:
        return jsonify({"error": "Missing customer_id or order_details"}), 400

    # Create new order record, order_date_time is set automatically
    new_order = Order(
        customer_id = customer_id,
        total_amount = 0
    )
    db.session.add(new_order)
    db.session.flush()

    total_amount = 0
    order_detail_objects = []
    for item in order_items:
        product = None

        # Check if product_id is provided & retrieve product
        if 'product_id' in item:
            product = Product.query.filter_by(id = item['product_id'], is_active=True).first()
        # If product_id not provided or not found, check product_name
        elif 'product_name' in item:
            product = Product.query.filter_by(name = item['product_name'], is_active=True).first()

        if not product:
            db.session.rollback()
            return jsonify({"error": "Product not found or not available"}), 400
        
        quantity = item.get('quantity')
        if quantity is None:
            return jsonify({"error": "Quantity is required for each order item"}), 400

        order_detail = OrderDetail(
            order_id = new_order.id,
            product_id = product.id,
            product_name = product.name,
            quantity = quantity,
            price_per_unit = float(product.price)
        )
        db.session.add(order_detail)
        order_detail_objects.append(order_detail)

        # Update Catalog stock
        catalog_entry = Catalog.query.filter_by(product_id=product.id).first()
        if catalog_entry:
            catalog_entry.product_stock -= quantity
            if catalog_entry.product_stock < 0:
                db.session.rollback()
                return jsonify({"error": f"Insufficient stock for {quantity} {product.name}"}), 400
            
        total_amount += quantity * float(product.price)

    new_order.total_amount = total_amount
    db.session.commit()

    order_details_data = order_details_schema.dump(order_detail_objects)
    return jsonify({
        "message": "Order placed successfully",
        "order_id": new_order.id,
        "order_date_time": new_order.order_date_time,
        "order_details": order_details_data,
        "total_amount": new_order.total_amount
    }), 201

@app.route('/orders/<int:id>', methods=['GET'])
def get_order_by_id(id):
    order = Order.query.get_or_404(id)
    if order:
        return order_schema.jsonify(order)

@app.route('/orders/track-status', methods=['POST'])
def track_order_by_id():
    order_id = request.args.get('order_id')
    customer_id = request.args.get('customer_id')
    order = Order.query.filter_by(id=order_id, customer_id=customer_id).first_or_404()
    if order:
        order_id = order_id
        customer_id = customer_id
        order_date_time = order.order_date_time
        expected_delivery_date = order_date_time.date()+timedelta(days=5)
        if order_date_time.date() <= date.today() < (order_date_time.date()+timedelta(days=3)):
            status = "Order in process"
        if (order_date_time.date()+timedelta(days=3)) <= date.today() < expected_delivery_date:
            status = "Shipped"
        if expected_delivery_date == date.today():
            status = "Out for delivery"
        if date.today() > expected_delivery_date:
            status = "Complete"

        return jsonify({
            "message": "Order tracking information",
            "customer_id": customer_id,
            "order_id": order_id,
            "order_date_time": order_date_time,
            "expected_delivery_date": expected_delivery_date,
            "status": status
        }), 200

# TODO BONUS retrieve order history for customer
@app.route('/orders/history-for-customer', methods=['POST'])
def get_order_history_by_customer_id():
    customer_id = request.args.get('customer_id')
    if not customer_id:
        return jsonify({"message": "Customer ID is required"}), 400
    
    try:
        orders = Order.query.filter_by(customer_id=customer_id).all()
    except Exception as e:
        return jsonify({
            "message": "An error occurred while fetching orders",
            "error": str(e)
            }), 500
    
    if orders:
        order_history = []

        for order in orders:
            order_data = {
                'order_id': order.id,
                'order_date_time': order.order_date_time,
                'total_amount': order.total_amount,
                'order_details': order_details_schema.dump(order.order_details)
            }
            order_history.append(order_data)

        return jsonify(order_history)
    else:
        return jsonify({"message": f"No order history associated with Customer ID: {customer_id}"}), 404


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)