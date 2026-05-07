import requests

BASE_URL = "http://127.0.0.1:8000"


def get_zones():
    """Fetch zones from API"""

    try:
        response = requests.get(f"{BASE_URL}/zones")
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Error fetching zones: {e}")
        return []


def get_products():
    """Fetch products from API"""

    try:
        response = requests.get(f"{BASE_URL}/products")
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Error fetching products: {e}")
        return []

def create_product(payload):
    """
    Create a new product via API
    """

    try:
        response = requests.post(
            f"{BASE_URL}/products",
            json=payload
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Error creating product: {e}")
        return None