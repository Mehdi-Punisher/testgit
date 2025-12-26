from abc import ABC, abstractmethod
import uuid

#  Product

class Product:
    def __init__(self, product_id, name, category, price, stock):
        self.id = product_id
        self.name = name
        self.category = category
        self.price = price
        self.stock = stock

    def reduce_stock(self, amount):
        if amount > self.stock:
            raise ValueError("Not enough stock")
        self.stock -= amount


#  Inventory

class Inventory:
    def __init__(self):
        self.products = {}

    def add_product(self, product):
        self.products[product.id] = product

    def list_products(self):
        return list(self.products.values())

    def find_by_id(self, product_id):
        return self.products.get(product_id)

    def search(self, keyword):
        keyword = keyword.lower()
        return [
            p for p in self.products.values()
            if keyword in p.name.lower() or keyword in p.category.lower()
        ]


#  CartItem

class CartItem:
    def __init__(self, product, quantity):
        self.product = product
        self.quantity = quantity

    @property
    def line_total(self):
        return self.product.price * self.quantity


#  ShoppingCart

class ShoppingCart:
    def __init__(self):
        self.items = {}

    def add_item(self, product, quantity):
        if quantity > product.stock:
            raise ValueError("Not enough stock")

        if product.id in self.items:
            new_quantity = self.items[product.id].quantity + quantity
            if new_quantity > product.stock:
                raise ValueError("Not enough stock")
            self.items[product.id].quantity = new_quantity
        else:
            self.items[product.id] = CartItem(product, quantity)

    def update_quantity(self, product_id, quantity):
        if product_id not in self.items:
            raise ValueError("Item not in cart")
        if quantity > self.items[product_id].product.stock:
            raise ValueError("Not enough stock")
        self.items[product_id].quantity = quantity

    def remove_item(self, product_id):
        self.items.pop(product_id, None)

    def calculate_total(self):
        return sum(item.line_total for item in self.items.values())

    def is_empty(self):
        return len(self.items) == 0

    def clear(self):
        self.items.clear()


# Discount Strategy (Abstract)

class DiscountStrategy(ABC):
    @abstractmethod
    def apply(self, total):
        pass


class NoDiscount(DiscountStrategy):
    def apply(self, total):
        return 0


class PercentageDiscount(DiscountStrategy):
    def __init__(self, percent):
        self.percent = percent

    def apply(self, total):
        return total * (self.percent / 100)


class FixedAmountDiscount(DiscountStrategy):
    def __init__(self, amount):
        self.amount = amount

    def apply(self, total):
        return min(total, self.amount)


class ThresholdPercentageDiscount(DiscountStrategy):
    def __init__(self, threshold, percent):
        self.threshold = threshold
        self.percent = percent

    def apply(self, total):
        if total >= self.threshold:
            return total * (self.percent / 100)
        return 0


# Order

class Order:
    def __init__(self, items, total_before, discount_amount, total_after):
        self.id = str(uuid.uuid4())[:8]
        self.items = items
        self.total_before = total_before
        self.discount_amount = discount_amount
        self.total_after = total_after


# User

class User:
    def __init__(self, name):
        self.name = name
        self.cart = ShoppingCart()
        self.orders = []

    def checkout(self, discount_strategy):
        if self.cart.is_empty():
            raise ValueError("Cart is empty")

        total_before = self.cart.calculate_total()
        discount_amount = discount_strategy.apply(total_before)
        total_after = total_before - discount_amount

        # reduce inventory stock
        for item in self.cart.items.values():
            item.product.reduce_stock(item.quantity)

        order = Order(
            items=list(self.cart.items.values()),
            total_before=total_before,
            discount_amount=discount_amount,
            total_after=total_after
        )

        self.orders.append(order)
        self.cart.clear()

        return order


# CLI Helpers

def print_products(products):
    print("\n=== Product List ===")
    for p in products:
        print(f"{p.id}) {p.name} | Category: {p.category} | Price: {p.price} | Stock: {p.stock}")
    print()


def print_cart(cart):
    if cart.is_empty():
        print("\nCart is empty.\n")
        return

    print("\n=== Cart ===")
    for item in cart.items.values():
        print(f"{item.product.name} | Qty: {item.quantity} | Line Total: {item.line_total}")
    print(f"Total: {cart.calculate_total()}\n")


def print_orders(orders):
    if len(orders) == 0:
        print("\nNo orders yet.\n")
        return

    print("\n=== Orders ===")
    for o in orders:
        print("-------------------------")
        print(f"Order ID: {o.id}")
        for item in o.items:
            print(f"- {item.product.name} x {item.quantity}")
        print(f"Total Before: {o.total_before}")
        print(f"Discount: {o.discount_amount}")
        print(f"Total After: {o.total_after}")
    print("-------------------------\n")


# Main Program

def main():
    inv = Inventory()
    inv.add_product(Product(1, "Tablet", "Digital", 2000, 5))
    inv.add_product(Product(2, "Computer", "Digital", 4000, 3))
    inv.add_product(Product(3, "Mouse", "Accessory", 550, 10))

    user = User("Default User")

    while True:
        print("""
        ========= SIMPLE SHOP CLI =========
        1) Show products
        2) Search products
        3) Add to cart
        4) Show cart
        5) Update/remove cart items
        6) Checkout
        7) Show orders
        0) Exit
        ===================================
""")

        choice = input("Select an option: ")

        if choice == "1":
            print_products(inv.list_products())

        elif choice == "2":
            keyword = input("Search keyword: ")
            print_products(inv.search(keyword))

        elif choice == "3":
            product_id = int(input("Product ID: "))
            quantity = int(input("Quantity: "))
            product = inv.find_by_id(product_id)
            if not product:
                print("Invalid product\n")
                continue

            try:
                user.cart.add_item(product, quantity)
                print("Added to cart.\n")
            except ValueError as e:
                print(str(e))

        elif choice == "4":
            print_cart(user.cart)

        elif choice == "5":
            print_cart(user.cart)
            product_id = int(input("Product ID: "))
            action = input("u = update quantity | d = delete: ").lower()

            if action == "u":
                qty = int(input("New quantity: "))
                try:
                    user.cart.update_quantity(product_id, qty)
                except ValueError as e:
                    print(str(e))

            elif action == "d":
                user.cart.remove_item(product_id)
                print("Removed.\n")

        elif choice == "6":
            print("""
            Choose discount:
            1) No discount
            2) Percentage
            3) Fixed amount
            4) Threshold percentage
""")
            opt = input("Select: ")

            if opt == "1":
                disc = NoDiscount()
            elif opt == "2":
                p = float(input("Percent: "))
                disc = PercentageDiscount(p)
            elif opt == "3":
                a = float(input("Amount: "))
                disc = FixedAmountDiscount(a)
            elif opt == "4":
                t = float(input("Threshold: "))
                p = float(input("Percent: "))
                disc = ThresholdPercentageDiscount(t, p)
            else:
                print("Invalid option\n")
                continue

            try:
                order = user.checkout(disc)
                print("\nCheckout complete!")
                print(f"Order ID: {order.id}")
                print(f"Before: {order.total_before}")
                print(f"Discount: {order.discount_amount}")
                print(f"After: {order.total_after}\n")
            except ValueError as e:
                print(str(e))

        elif choice == "7":
            print_orders(user.orders)

        elif choice == "0":
            print("Goodbye!")
            break

        else:
            print("Invalid option\n")


# Run
main()