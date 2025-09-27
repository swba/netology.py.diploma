import secrets
import string

from rest_framework.response import Response

def assert_response(response: Response, status: int, json: dict) -> dict:
    """Asserts API response.

    Args:
        response: API response.
        status: Expected HTTP status code.
        json: Expected JSON response.

    Returns:
        Response JSON.
    """
    assert response.status_code == status
    assert response.json() == json
    return response.json()

def generate_password() -> str:
    """Generates an eight-character alphanumeric password."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(8))
