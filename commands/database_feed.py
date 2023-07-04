from typing import Any, List
import requests
import json
import random


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


class Call:
    count = 1

    def __init__(self, *, base_url, debug=True) -> None:
        self.headers = {}
        self.base_url = base_url
        self.debug = debug

    def _log_start(self, method, url, *, force=False):
        if self.debug and force:
            url = url.replace(self.base_url, "")
            print(f'[{Call.count}] {method} {url} Started')

    def _log_end(self, method, url, response):
        if self.debug:
            url = url.replace(self.base_url, "")
            print(f'[{Call.count}] {method} {url} End: ', response.json())

    def add_header(self, key, value):
        self.headers[key] = value

    def request(self, method, url, *args, **kargs):
        response = None
        try:
            self._log_start(method, url)
            response = requests.request(method, url, *args, **kargs)
            self._log_end(method, url, response)
            Call.count += 1
            return response
        except Exception as e:
            self._log_start(method, url, force=True)
            print("Error: ", response)
            raise e

    def get(self, url, *args, **kargs):
        return self.request("GET", url, *args, **kargs)

    def post(self, url, *args, **kargs):
        return self.request("POST", url, *args, **kargs)

    def put(self, url, *args, **kargs):
        return self.request("PUT", url, *args, **kargs)


class MockerAdmin:
    def __init__(self, ctx: Context, base_url: str, save_images: bool) -> None:
        self.ctx = ctx
        self.call = Call(base_url=base_url)
        self.admin = {
            "password": "123",
            "name": "Admin",
            "email": "admin@safeeat.com",
            "cellphone": "999222111",
            "restrictionIds": [],
        }
        self.executions = []
        self.base_url = base_url
        self.save_images = save_images

    def _check_dependencies(self, current, dependencies):
        if all(it in self.executions for it in dependencies):
            self.executions.append(current)
            return True
        raise Exception(
            f"MockerAdmin: '{current}' depends on {dependencies}, but {self.executions} were executed")

    def _signup(self):
        self.call.post(f"{self.base_url}/signup", json=self.admin).json()

    def _login(self):
        token = self.call.post(f"{self.base_url}/login", json={
            "email": self.admin['email'],
            "password": self.admin['password']
        }).json()['token']
        self.call.add_header("Authorization", f"Bearer {token}")

    def _add_restrictions(self):
        self._check_dependencies("restrictions", [])
        self.call.debug = False
        for restriction in Mock.restrictions:
            response = self.call.post(f"{self.base_url}/restrictions",
                                      json=restriction, headers=self.call.headers)
        response = self.call.get(f"{self.base_url}/restrictions")
        self.ctx.add_all("restrictions", response.json())
        print("Restrictions Count: ", len(response.json()))
        print()
        self.call.debug = True

    def _update_category_image(self, category, extras):
        if not self.save_images:
            return
        files = {"image": open("./images/categories/" +
                               extras.get("image"), "rb")}
        self.call.put(f"{self.base_url}/categories/{category['id']}/image",
                      files=files, headers=self.call.headers)

    def _add_advertisements(self, restaurant, extras):
        restaurant_id = restaurant["id"]
        self.call.debug = False
        for advertisement in extras.get("advertisements", []):
            self.call.post(f"{self.base_url}/advertisements", json={
                "title": advertisement,
                "restaurantId": restaurant_id,
            }, headers=self.call.headers)
            # TODO: Add image
        response = self.call.get(
            f"{self.base_url}/advertisements/restaurant/{restaurant_id}", headers=self.call.headers)
        print("Advertisements Count: ", len(response.json()))
        self.call.debug = True
        print()

    def _add_deliveries(self, restaurant, extras):
        restaurantId = restaurant["id"]
        self.call.debug = False
        for delivery in Mock.deliveries:
            self.call.post(f"{self.base_url}/deliveries/restaurant/{restaurantId}",
                           json=delivery, headers=self.call.headers)
        response = self.call.get(f"{self.base_url}/deliveries/restaurant/{restaurantId}",
                                 headers=self.call.headers)
        print("Deliveries Count: ", len(response.json()))
        self.call.debug = True
        print()

    def _add_restaurants(self):
        self._check_dependencies("restaurants", [])
        for restaurant in Mock.restaurants:
            restaurant = dict(restaurant)
            extras = restaurant["$$"]
            del restaurant["$$"]

            self.call.debug = False
            response = self.call.post(f"{self.base_url}/restaurants",
                                      json=restaurant, headers=self.call.headers)
            try:
                response = response.json()
                print("Restaurant: ", response["name"])
                self._add_advertisements(response, extras)
                self._add_deliveries(response, extras)
            except:
                print("Restaurant already exists: ", restaurant["name"])

        self.call.debug = False
        response = self.call.get(
            f"{self.base_url}/restaurants", headers=self.call.headers)
        self.ctx.add_all("restaurants", response.json())
        print("Restaurants Count: ", len(response.json()))
        print()
        self.call.debug = True

    def _add_restaurants_sections(self, *, depends=[]):
        self._check_dependencies("restaurants_sections", depends)
        self.call.debug = False
        for section in Mock.restaurants_sections:
            extras = section["$$"]
            del section["$$"]
            restaurant_ids = [self.ctx.get_id('restaurants', lambda it: it['name'] == name)
                              for name in extras.get("restaurants", [])]
            section["restaurantIds"] = restaurant_ids
            response = self.call.post(f"{self.base_url}/restaurantSections",
                                      json=section, headers=self.call.headers)
            section = response.json()
        response = self.call.get(f"{self.base_url}/restaurantSections",
                                 headers=self.call.headers)
        print("Restaurant Sections Count: ", len(response.json()))
        print()
        self.call.debug = True

    def _add_categories(self):
        self._check_dependencies("categories", [])
        for category in Mock.categories:
            category = dict(category)
            self.call.debug = False
            extras = category["$$"]
            del category["$$"]
            response = self.call.post(f"{self.base_url}/categories",
                                      json=category, headers=self.call.headers)
            category = response.json()
            self._update_category_image(category, extras)

        self.call.debug = False
        response = self.call.get(
            f"{self.base_url}/categories", headers=self.call.headers)
        self.ctx.add_all("categories", response.json())
        print("Categories Count: ", len(response.json()))
        print()
        self.call.debug = True

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
        self.call.debug = False
        for ingredient in all_ingredients:
            extras = ingredient["$$"]
            del ingredient["$$"]
            restaurantId = extras["restaurantId"]
            self.call.post(f"{self.base_url}/ingredients/restaurant/{restaurantId}",
                           json=ingredient, headers=self.call.headers)
        response = self.call.get(f"{self.base_url}/ingredients",
                                 headers=self.call.headers)
        self.ctx.add_all("ingredients", response.json())
        print("Ingredients Count: ", len(response.json()))
        print()
        self.call.debug = True

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
        self.call.debug = False
        for product in all_products:
            extras = product["$$"]
            del product["$$"]
            restaurantId = extras["restaurantId"]
            self.call.post(f"{self.base_url}/products/restaurant/{restaurantId}",
                           json=product, headers=self.call.headers)
        response = self.call.get(f"{self.base_url}/products",
                                 headers=self.call.headers)
        self.ctx.add_all("products", response.json())
        print("Products Count: ", len(response.json()))
        print()

    def _add_product_sections(self, *, depends=[]):
        self._check_dependencies("product_sections", depends)
        self.call.debug = False
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
                self.call.post(f"{self.base_url}/productSections/restaurant/{restaurantId}",
                               json=data, headers=self.call.headers)
        response = self.call.get(
            f"{self.base_url}/productSections", headers=self.call.headers)
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
        self.call = Call(base_url=base_url)
        self.base_url = base_url
        self.save_images = save_images

    def _signup(self, user: dict, extras: dict):
        restrictions_ids = [self.ctx.get_id("restrictions", lambda it: it['name'] == name)
                            for name in extras.get("restrictions", [])]
        user["restrictionIds"] = restrictions_ids
        self.call.post(f"{self.base_url}/signup", json=user)
        print()

    def _login(self, user: dict, extras: dict):
        token = self.call.post(f"{self.base_url}/login", json={
            "email": user['email'],
            "password": user['password']
        }).json()['token']
        self.call.add_header("Authorization", f"Bearer {token}")
        print()

    def _upload_image(self, user: dict, extras: dict):
        if not self.save_images:
            return
        files = {"image": open("./images/users/" + extras.get("photo"), "rb")}
        self.call.put(f"{self.base_url}/users/me/image",
                      files=files, headers=self.call.headers)
        print()

    def _add_addresses(self, user: dict, extras: dict):
        self.call.debug = False
        for it in extras.get("addresses", []):
            self.call.post(f"{self.base_url}/addresses", json=it,
                           headers=self.call.headers)
        result = self.call.get(f"{self.base_url}/addresses/user/me",
                               headers=self.call.headers)
        print("Addresses Count: ", len(result.json()))
        print()
        self.call.debug = True

    def _add_payments(self, user: dict, extras: dict):
        self.call.debug = False
        count = extras.get("payments", 0)
        for it in Mock.payments[0:count]:
            self.call.post(f"{self.base_url}/payments", json=it,
                           headers=self.call.headers)
        result = self.call.get(f"{self.base_url}/payments/user/me",
                               headers=self.call.headers)
        print("Payments Count: ", len(result.json()))
        print()

        self.call.debug = True

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

    print(f"Done using {Call.count} requests")
