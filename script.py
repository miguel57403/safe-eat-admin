from typing import Any
import requests
import json

# BASE_URL = "https://safe-eat-api.azurewebsites.net"
BASE_URL = "http://localhost:8080"


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


class Context:
    def __init__(self) -> None:
        self.entities = {}

    def add(self, key, value):
        self.add_all(key, [value])

    def add_all(self, key, values):
        self.entities[key] = self.entities.get(key, []) + values

    def get_id(self, key, predicate):
        for it in self.entities.get(key, []):
            if predicate(it):
                return it['id']
        raise Exception(f"Entity with predicate {predicate} not found")


class Call:
    count = 1

    def __init__(self, *, debug=True) -> None:
        self.headers = {}
        self.debug = debug

    def _log_start(self, method, url, *, force=False):
        if self.debug and force:
            url = url.replace(BASE_URL, "")
            print(f'[{Call.count}] {method} {url} Started')

    def _log_end(self, method, url, response):
        if self.debug:
            url = url.replace(BASE_URL, "")
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
    def __init__(self, ctx: Context) -> None:
        self.ctx = ctx
        self.call = Call()
        self.admin = {
            "password": "123",
            "name": "Admin",
            "email": "admin@safeeat.com",
            "cellphone": "999222111",
            "restrictionIds": [],
        }
        self.send_images = False

    def _signup(self):
        self.call.post(f"{BASE_URL}/signup", json=self.admin).json()

    def _login(self):
        token = self.call.post(f"{BASE_URL}/login", json={
            "email": self.admin['email'],
            "password": self.admin['password']
        }).json()['token']
        self.call.add_header("Authorization", f"Bearer {token}")

    def _add_restrictions(self):
        self.call.debug = False
        for restriction in Mock.restrictions:
            response = self.call.post(f"{BASE_URL}/restrictions",
                                      json=restriction, headers=self.call.headers)
        response = self.call.get(f"{BASE_URL}/restrictions")
        self.ctx.add_all("restrictions", response.json())
        print("Restrictions Count: ", len(response.json()))
        print()
        self.call.debug = True

    def _update_category_image(self, category, extras):
        if not self.send_images:
            return
        files = {"image": open("./images/categories/" +
                               extras.get("image"), "rb")}
        self.call.put(f"{BASE_URL}/categories/{category['id']}/image",
                      files=files, headers=self.call.headers)

    def _add_advertisements(self, restaurant, extras):
        restaurant_id = restaurant["id"]
        self.call.debug = False
        for advertisement in extras.get("advertisements", []):
            self.call.post(f"{BASE_URL}/advertisements", json={
                "title": advertisement["title"],
                "restaurantId": restaurant_id,
            }, headers=self.call.headers)
        response = self.call.get(
            f"{BASE_URL}/advertisements/restaurant/{restaurant_id}", headers=self.call.headers)
        print("Advertisements Count: ", len(response.json()))
        self.call.debug = True
        print()

    def _add_restaurants(self):
        for restaurant in Mock.restaurants:
            self.call.debug = False
            extras = restaurant["$$"]
            del restaurant["$$"]

            response = self.call.post(f"{BASE_URL}/restaurants",
                                      json=restaurant, headers=self.call.headers)
            restaurant = response.json()
            print("Restaurant: ", restaurant["name"])
            self.ctx.add("restaurants", restaurant)
            self._add_advertisements(restaurant, extras)
            self.call.debug = True

        self.call.debug = False
        response = self.call.get(
            f"{BASE_URL}/restaurants", headers=self.call.headers)
        self.ctx.add_all("restaurants", response.json())
        print("Restaurants Count: ", len(response.json()))
        print()
        self.call.debug = True

    def _add_restaurants_sections(self):
        self.call.debug = False
        for section in Mock.restaurants_sections:
            self.call.debug = False
            extras = section["$$"]
            del section["$$"]
            restaurant_ids = [self.ctx.get_id('restaurants', lambda it: it['name'] == name)
                              for name in extras.get("restaurants", [])]
            section["restaurantIds"] = restaurant_ids
            response = self.call.post(f"{BASE_URL}/restaurantSections",
                                      json=section, headers=self.call.headers)
            section = response.json()
            print("Section: ", section["name"])
            self.call.debug = True
        self.call.debug = True

    def _add_categories(self):
        for category in Mock.categories:
            self.call.debug = False
            extras = category["$$"]
            del category["$$"]
            response = self.call.post(f"{BASE_URL}/categories",
                                      json=category, headers=self.call.headers)
            category = response.json()
            self._update_category_image(category, extras)
            self.call.debug = True

        self.call.debug = False
        response = self.call.get(
            f"{BASE_URL}/categories", headers=self.call.headers)
        self.ctx.add_all("categories", response.json())
        print("categories Count: ", len(response.json()))
        print()
        self.call.debug = True

    def execute(self):
        self._signup()
        self._login()
        self._add_restrictions()
        self._add_restaurants()
        self._add_restaurants_sections()
        self._add_categories()


class MockerUser:
    def __init__(self, ctx: Context) -> None:
        self.ctx = ctx
        self.call = Call()
        self.send_images = False

    def _signup(self, user: dict, extras: dict):
        restrictions_ids = [self.ctx.get_id("restrictions", lambda it: it['name'] == name)
                            for name in extras.get("restrictions", [])]
        user["restrictionIds"] = restrictions_ids
        self.call.post(f"{BASE_URL}/signup", json=user)
        print()

    def _login(self, user: dict, extras: dict):
        token = self.call.post(f"{BASE_URL}/login", json={
            "email": user['email'],
            "password": user['password']
        }).json()['token']
        self.call.add_header("Authorization", f"Bearer {token}")
        print()

    def _upload_image(self, user: dict, extras: dict):
        if not self.send_images:
            return
        files = {"image": open("./images/users/" + extras.get("photo"), "rb")}
        self.call.put(f"{BASE_URL}/users/me/image",
                      files=files, headers=self.call.headers)
        print()

    def _add_addresses(self, user: dict, extras: dict):
        self.call.debug = False
        for it in extras.get("addresses", []):
            self.call.post(f"{BASE_URL}/addresses", json=it,
                           headers=self.call.headers)
        result = self.call.get(f"{BASE_URL}/addresses/user/me",
                               headers=self.call.headers)
        print("Addresses Count: ", len(result.json()))
        print()
        self.call.debug = True

    def _add_payments(self, user: dict, extras: dict):
        self.call.debug = False
        count = extras.get("payments", 0)
        for it in Mock.payments[0:count]:
            self.call.post(f"{BASE_URL}/payments", json=it,
                           headers=self.call.headers)
        result = self.call.get(f"{BASE_URL}/payments/user/me",
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


ctx = Context()
admin = MockerAdmin(ctx)
admin.execute()

for it in Mock.users:
    user = MockerUser(ctx)
    user.execute(it)
