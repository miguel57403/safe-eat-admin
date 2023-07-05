import json
import random
from .api import Api


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


class Context:
    def __init__(self) -> None:
        self.entities = {}

    def add(self, key, value):
        self.add_all(key, [value])

    def add_all(self, key, values):
        self.entities[key] = self.entities.get(key, []) + values

    def get_id(self, key, predicate):
        result = self.get_id_unsafe(key, predicate)
        if result is None:
            raise Exception(f"Entity with predicate not found")
        return result

    def get_id_unsafe(self, key, predicate):
        for it in self.entities[key]:
            if predicate(it):
                return it['id']

    def get_id_by_name(self, key, name):
        for it in self.entities[key]:
            if it['name'] == name:
                return it['id']
        raise Exception(f"Entity in '{key}' with name '{name}' not found")

    def get_id_by_dict(self, key, data):
        result = self.get_id_by_dict_unsafe(key, data)
        if result is None:
            raise Exception(f"Entity in '{key}' with data '{data}' not found")
        return result

    def get_id_by_dict_unsafe(self, key, data):
        for it in self.entities[key]:
            if all(it[k] == data[k] for k in data.keys()):
                return it['id']


class MockerAdmin:
    def __init__(self, ctx: Context, base_url: str, save_images: bool) -> None:
        self.ctx = ctx
        self.api = Api.create(base_url=base_url)
        self.admin = {
            "password": "123",
            "name": "Admin",
            "email": "admin@safeeat.com",
            "cellphone": "999222111",
            "restrictionIds": [],
        }
        self.executions = []
        self.save_images = save_images

    def _check_dependencies(self, current, dependencies):
        if all(it in self.executions for it in dependencies):
            self.executions.append(current)
            return True
        raise Exception(
            f"MockerAdmin: '{current}' depends on {dependencies}, but {self.executions} were executed")

    def _signup(self):
        self.api.signup(self.admin)

    def _login(self):
        body = {"email": self.admin['email'],
                "password": self.admin['password']}
        token = self.api.login(body).json()['token']
        self.api.add_header("Authorization", f"Bearer {token}")

    def _add_restrictions(self):
        self._check_dependencies("restrictions", [])
        self.api.debug = False
        for restriction in Mock.restrictions:
            response = self.api.restrictions_store(restriction)
        response = self.api.restrictions_index()
        self.ctx.add_all("restrictions", response.json())
        print("Restrictions Count: ", len(response.json()))
        print()
        self.api.debug = True

    def _update_category_image(self, category, extras):
        if not self.save_images:
            return

        with open("./images/categories/" + extras.get("image"), "rb") as image:
            self.api.categories_update_image(category['id'], image)

    def _add_advertisements(self, restaurant, extras):
        restaurant_id = restaurant["id"]
        self.api.debug = False
        for advertisement in extras.get("advertisements", []):
            self.api.advertisements_store({
                "title": advertisement, "restaurantId": restaurant_id})
            # TODO: Add image
        response = self.api.advertisements_index_by_restaurant(restaurant_id)
        print("Advertisements Count: ", len(response.json()))
        self.api.debug = True
        print()

    def _add_deliveries(self, restaurant, extras):
        restaurantId = restaurant["id"]
        self.api.debug = False
        for delivery in Mock.deliveries:
            self.api.deliveries_store(restaurantId, delivery)
        response = self.api.deliveries_index_by_restaurant(restaurantId)
        print("Deliveries Count: ", len(response.json()))
        self.api.debug = True
        print()

    def _add_restaurants(self):
        self._check_dependencies("restaurants", [])
        for restaurant in Mock.restaurants:
            restaurant = dict(restaurant)
            extras = restaurant["$$"]
            del restaurant["$$"]

            self.api.debug = False
            response = self.api.restaurants_store(restaurant)
            try:
                response = response.json()
                print("Restaurant: ", response["name"])
                self._add_advertisements(response, extras)
                self._add_deliveries(response, extras)
            except:
                print("Restaurant already exists: ", restaurant["name"])

        self.api.debug = False
        response = self.api.restaurants_index()
        self.ctx.add_all("restaurants", response.json())
        print("Restaurants Count: ", len(response.json()))
        print()
        self.api.debug = True

    def _add_restaurants_sections(self, *, depends=[]):
        self._check_dependencies("restaurants_sections", depends)
        self.api.debug = False
        for section in Mock.restaurants_sections:
            extras = section["$$"]
            del section["$$"]
            restaurant_ids = [self.ctx.get_id_by_name('restaurants', name)
                              for name in extras.get("restaurants", [])]
            section["restaurantIds"] = restaurant_ids
            self.api.restaurant_sections_store(section)
        response = self.api.restaurant_sections_index()
        print("Restaurant Sections Count: ", len(response.json()))
        print()
        self.api.debug = True

    def _add_categories(self):
        self._check_dependencies("categories", [])
        for category in Mock.categories:
            category = dict(category)
            self.api.debug = False
            extras = category["$$"]
            del category["$$"]
            category = self.api.categories_store(category).json()
            self._update_category_image(category, extras)

        self.api.debug = False
        response = self.api.categories_index().json()
        self.ctx.add_all("categories", response)
        print("Categories Count: ", len(response))
        print()
        self.api.debug = True

    def _add_ingredients(self, *, depends=[]):
        self._check_dependencies("ingredients", depends)
        # Collect all ingredients
        all_ingredients = []
        for restaurant in Mock.restaurants:
            restaurant = dict(restaurant)
            restaurantId = self.ctx.get_id_by_name(
                "restaurants", restaurant["name"])

            products_names = []
            for products in restaurant["$$"]['productSections'].values():
                products_names.extend(products)
            products_names = set(products_names)

            ingredients_names = []
            for product in products_names:
                product = Mock.find_product(name=product)
                ingredients_names.extend(product["$$"]["ingredients"])
            ingredients_names = set(ingredients_names)

            for ingredient in ingredients_names:
                ingredient = Mock.find_ingredient(name=ingredient)
                ingredient["description"] = ingredient["name"]
                restrictions = Mock.ingredients_restrictions[ingredient['name']]
                restriction_ids = [self.ctx.get_id_by_name("restrictions", restriction)
                                   for restriction in restrictions]
                ingredient["restrictionIds"] = restriction_ids
                ingredient["$$"] = {"restaurantId": restaurantId}
                all_ingredients.append(ingredient)

        # Add ingredients
        self.api.debug = False
        for ingredient in all_ingredients:
            extras = ingredient["$$"]
            del ingredient["$$"]
            restaurantId = extras["restaurantId"]
            self.api.ingredients_store(restaurantId, ingredient)
        response = self.api.ingredients_index()
        print(response)
        response = response.json()
        self.ctx.add_all("ingredients", response)
        print("Ingredients Count: ", len(response))
        print()
        self.api.debug = True

    def _add_products(self, *, depends=[]):
        self._check_dependencies("products", depends)

        # Collect all products
        all_products = []
        for restaurant in Mock.restaurants:
            restaurant = dict(restaurant)
            restaurantId = self.ctx.get_id_by_name(
                "restaurants", restaurant["name"])

            products_names = []
            for products in restaurant["$$"]['productSections'].values():
                products_names.extend(products)
            products_names = set(products_names)

            for product in products_names:
                product = Mock.find_product(name=product)
                extras = product["$$"]
                del product["$$"]
                product['price'] = random.random() * 100
                product['categoryId'] = self.ctx.get_id_by_name(
                    "categories", extras['category'])
                product['ingredientIds'] = [
                    self.ctx.get_id_by_dict(
                        "ingredients", {"name": ingredient, "restaurantId": restaurantId})
                    for ingredient in extras.get("ingredients", [])]
                product["$$"] = {"restaurantId": restaurantId}
                all_products.append(product)

        # Add products
        self.api.debug = False
        for product in all_products:
            extras = product["$$"]
            del product["$$"]
            restaurantId = extras["restaurantId"]
            self.api.products_store(restaurantId, product)
        response = self.api.products_index().json()
        self.ctx.add_all("products", response)
        print("Products Count: ", len(response))
        print()

    def _add_product_sections(self, *, depends=[]):
        self._check_dependencies("product_sections", depends)
        self.api.debug = False
        for restaurant in Mock.restaurants:
            restaurant = dict(restaurant)
            for section, products in restaurant["$$"]["productSections"].items():
                restaurantId = self.ctx.get_id_by_name(
                    'restaurants', restaurant['name'])
                product_ids = [
                    self.ctx.get_id_by_dict(
                        'products', {"name": product, "restaurantId": restaurantId})
                    for product in products]
                data = {"name": section, "productIds": product_ids}
                self.api.product_sections_store(restaurantId, data)
        response = self.api.product_sections_index()
        self.ctx.add_all("product_sections", response.json())
        print("Product Sections Count: ", len(response.json()))
        print()

    def execute(self):
        self._signup()
        self._login()
        self._add_restrictions()
        self._add_restaurants()
        self._add_restaurants_sections(depends=["restaurants"])
        self._add_categories()
        self._add_ingredients(depends=["restrictions", "restaurants"])
        self._add_products(depends=["categories", "ingredients"])
        self._add_product_sections(depends=["products"])


class MockerUser:
    def __init__(self, ctx: Context, base_url: str, save_images: bool) -> None:
        self.ctx = ctx
        self.api = Api.create(base_url=base_url)
        self.save_images = save_images

    def _signup(self, user: dict, extras: dict):
        restrictions_ids = [self.ctx.get_id("restrictions", lambda it: it['name'] == name)
                            for name in extras.get("restrictions", [])]
        user["restrictionIds"] = restrictions_ids
        self.api.signup(user)
        print()

    def _login(self, user: dict, extras: dict):
        token = self.api.login(
            {"email": user['email'], "password": user['password']}).json()['token']
        self.api.add_header("Authorization", f"Bearer {token}")
        print()

    def _upload_image(self, user: dict, extras: dict):
        if not self.save_images:
            return
        with open("./images/users/" + extras.get("photo"), "rb") as image:
            self.api.users_upload_image(image)
        print()

    def _add_addresses(self, user: dict, extras: dict):
        self.api.debug = False
        for it in extras.get("addresses", []):
            self.api.addresses_store(it)
        result = self.api.addresses_index_me().json()
        print("Addresses Count: ", len(result))
        print()
        self.api.debug = True

    def _add_payments(self, user: dict, extras: dict):
        self.api.debug = False
        count = extras.get("payments", 0)
        for it in Mock.payments[0:count]:
            self.api.payments_store(it)
        result = self.api.payments_index_me().json()
        print("Payments Count: ", len(result))
        print()

        self.api.debug = True

    def execute(self, user: dict):
        extras = user["$$"]
        del user["$$"]
        self._signup(user, extras)
        self._login(user, extras)
        self._upload_image(user, extras)
        self._add_addresses(user, extras)
        self._add_payments(user, extras)


def database_feed(base_url: str, save_images: bool):
    ctx = Context()
    admin = MockerAdmin(ctx, base_url, save_images)
    admin.execute()

    for it in Mock.users:
        user = MockerUser(ctx, base_url, save_images)
        user.execute(it)

    print(f"Done using {Api.count} requests")
