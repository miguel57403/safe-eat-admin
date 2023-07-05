import requests


class HttpClient:
    count = 1

    def __init__(self, *, base_url, debug=True) -> None:
        self.headers = {}
        self.base_url = base_url
        self.debug = debug

    def _log_start(self, method, url, *, force=False):
        if True or self.debug and force:
            print(f'API: [{HttpClient.count}] {method} {url}')

    def _log_end(self, method, url, response):
        if self.debug and False:
            print(
                f'API: [{HttpClient.count}] {method} {url} End: ', response.json())

    def add_header(self, key, value):
        self.headers[key] = value

    def request(self, method, url, *args, **kargs):
        response = None
        try:
            self._log_start(method, url)
            response = requests.request(method, url, *args, **kargs)
            self._log_end(method, url, response)
            HttpClient.count += 1
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


class Api:
    @staticmethod
    def create(*, base_url, debug=True):
        return Api(HttpClient(base_url=base_url, debug=debug))

    @staticmethod
    def count():
        return HttpClient.count

    def __init__(self, client: HttpClient):
        self.base_url = client.base_url
        self.client = client

    def add_header(self, key, value):
        self.client.add_header(key, value)

    @property
    def debug(self):
        return self.client.debug

    @debug.setter
    def debug(self, value):
        self.client.debug = value

    def signup(self, data: dict):
        return self.client.post(f"{self.base_url}/signup", json=data)

    def login(self, data: dict):
        return self.client.post(f"{self.base_url}/login", json=data)

    # addresses
    def addresses_index_me(self):
        return self.client.get(f"{self.base_url}/addresses/user/me", headers=self.client.headers)

    def addresses_store(self, data: dict):
        return self.client.post(f"{self.base_url}/addresses", json=data, headers=self.client.headers)

    # advertisements
    def advertisements_index_by_restaurant(self, restaurant_id: str):
        return self.client.get(f"{self.base_url}/advertisements/restaurant/{restaurant_id}", headers=self.client.headers)

    def advertisements_store(self, data: dict):
        return self.client.post(f"{self.base_url}/advertisements", json=data, headers=self.client.headers)

    # categories
    def categories_index(self):
        return self.client.get(f"{self.base_url}/categories", headers=self.client.headers)

    def categories_store(self, data: dict):
        return self.client.post(f"{self.base_url}/categories", json=data, headers=self.client.headers)

    def categories_update_image(self, category_id: str, image):
        return self.client.put(f"{self.base_url}/categories/{category_id}/image", files={"image": image}, headers=self.client.headers)

    # deliveries
    def deliveries_index_by_restaurant(self, restaurant_id: str):
        return self.client.get(f"{self.base_url}/deliveries/restaurant/{restaurant_id}")

    def deliveries_store(self, restaurant_id: str, data: dict):
        return self.client.post(f"{self.base_url}/deliveries/restaurant/{restaurant_id}", json=data, headers=self.client.headers)

    # ingredients
    def ingredients_index(self):
        return self.client.get(f"{self.base_url}/ingredients", headers=self.client.headers)

    def ingredients_store(self, restaurant_id: str, data: dict):
        return self.client.post(f"{self.base_url}/ingredients/restaurant/{restaurant_id}", json=data, headers=self.client.headers)

    # payments
    def payments_index_me(self):
        return self.client.get(f"{self.base_url}/payments/user/me", headers=self.client.headers)

    def payments_store(self, data: dict):
        return self.client.post(f"{self.base_url}/payments", json=data, headers=self.client.headers)

    # products
    def products_index(self):
        return self.client.get(f"{self.base_url}/products", headers=self.client.headers)

    def products_store(self, restaurant_id: str, data: dict):
        return self.client.post(f"{self.base_url}/products/restaurant/{restaurant_id}", json=data, headers=self.client.headers)

    # productSections
    def product_sections_index(self):
        return self.client.get(f"{self.base_url}/productSections", headers=self.client.headers)

    def product_sections_store(self, restaurant_id: str, data: dict):
        return self.client.post(f"{self.base_url}/productSections/restaurant/{restaurant_id}", json=data, headers=self.client.headers)

    # restaurants
    def restaurants_index(self):
        return self.client.get(f"{self.base_url}/restaurants", headers=self.client.headers)

    def restaurants_store(self, data: dict):
        return self.client.post(f"{self.base_url}/restaurants", json=data, headers=self.client.headers)

    # restaurantSections
    def restaurant_sections_index(self):
        return self.client.get(f"{self.base_url}/restaurantSections", headers=self.client.headers)

    def restaurant_sections_store(self, data: dict):
        return self.client.post(f"{self.base_url}/restaurantSections", json=data, headers=self.client.headers)

    # restrictions
    def restrictions_index(self):
        return self.client.get(f"{self.base_url}/restrictions")

    def restrictions_store(self, data: dict):
        return self.client.post(f"{self.base_url}/restrictions", json=data, headers=self.client.headers)

    # users
    def users_upload_image(self, image):
        return self.client.put(f"{self.base_url}/users/me/image", files={'image': image}, headers=self.client.headers)
