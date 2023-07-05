from .api import Api
from .mock import Mock
from pathlib import Path
import random


def _login_admin(api: Api):
    token = api.login({"email": "admin@safeeat.com",
                      "password": "123"}).json()['token']
    api.add_header("Authorization", f"Bearer {token}")


def advertisements(url):
    api: Api = Api.create(base_url=url)
    _login_admin(api)

    paths = Path('images/advertisements').glob('*')

    restaurants = api.restaurants_index().json()
    for restaurant in restaurants:
        advertisements = api.advertisements_index_by_restaurant(
            restaurant['id']).json()
        for advertisement in advertisements:
            with random.choice(paths).open('rb') as image:
                response = api.advertisements_update_image(
                    advertisement['id'], image)
                if response.status_code != 200:
                    ad_id = advertisement['id']
                    raise Exception(f"Fail to upload image: {ad_id}")


def restaurants(url):
    api = Api.create(base_url=url)
    _login_admin(api)

    paths = list(Path('images/restaurants').glob('*'))

    restaurants = api.restaurants_index().json()
    for restaurant in restaurants:
        with random.choice(paths).open('rb') as image:
            api.restaurants_update_cover(restaurant['id'], image)
            api.restaurants_update_logo(restaurant['id'], image)
