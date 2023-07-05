import json


def load_json(path):
    with open(path, 'r', encoding="utf-8") as f:
        return json.load(f)


class Mock:
    restrictions = load_json('./data/restrictions.json')
    users = load_json('./data/users.json')
    payments = load_json('./data/payments.json')
    restaurants = load_json('./data/restaurants.json')
    categories = load_json('./data/categories.json')
    restaurants_sections = load_json('./data/restaurants_sections.json')
    deliveries = load_json('./data/deliveries.json')
    products = load_json('./data/products.json')
    ingredients = load_json('./data/ingredients.json')
    ingredients_restrictions = load_json(
        "./data/ingredients_restrictions.json")

    @staticmethod
    def find_product(*, name):
        for product in Mock.products:
            if product['name'] == name:
                return dict(product)
        raise Exception(f"Product with name {name} not found")

    @staticmethod
    def find_category(*, name):
        for category in Mock.categories:
            if category['name'] == name:
                return dict(category)
        raise Exception(f"Category with name {name} not found")

    @staticmethod
    def find_ingredient(*, name):
        for ingredient in Mock.ingredients:
            if ingredient['name'] == name:
                return dict(ingredient)
        raise Exception(f"Ingredient with name {name} not found")
