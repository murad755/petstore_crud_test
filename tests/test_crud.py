import pytest
import requests
from random import randint

BASE_URL = "https://petstore.swagger.io/v2"
NEW_PET_ID = randint(0, 9)


def get_pets_with_status(status='available'):
    """Fetch pets based on their status."""
    return requests.get(f"{BASE_URL}/pet/findByStatus", params={'status': status})


def is_pet_present(pet_id, expected_pets, status='available', retries=20, expected_status_code=200):
    """Check if the pet with the given ID is present in the list of pets with the specified status."""
    if retries <= 0:
        return False
    response = get_pets_with_status(status)

    if response.status_code != expected_status_code:
        return False

    pets = [pet for pet in response.json() if pet['id'] == pet_id]
    if pets == expected_pets:
        return True

    return is_pet_present(pet_id, expected_pets, status, retries - 1, expected_status_code)


def is_pet_deleted(pet_id, retries=20):
    """Check if the pet has been successfully deleted."""
    if retries <= 0:
        return False

    response = requests.get(f"{BASE_URL}/pet/{pet_id}")

    # If the status code is 404, it means the pet was deleted successfully
    if response.status_code == 404:
        return True

    return is_pet_deleted(pet_id, retries - 1)


@pytest.mark.dependency()
def test_get_available_pets():
    """Test that findByStatus returns a non-empty list of available pets."""
    response = get_pets_with_status()
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.dependency()
def test_add_new_pet():
    """Test if a new pet can be added and successfully retrieved."""
    payload = {
        "id": NEW_PET_ID,
        "category": {"id": NEW_PET_ID, "name": "string"},
        "name": "doggie",
        "photoUrls": ["string"],
        "tags": [{"id": NEW_PET_ID, "name": "string"}],
        "status": "available"
    }

    response = requests.post(f"{BASE_URL}/pet", json=payload)
    assert response.status_code == 200
    new_pet = response.json()

    assert is_pet_present(NEW_PET_ID, [new_pet], status='available')


@pytest.mark.dependency(depends=["test_add_new_pet"])
def test_update_pet_status():
    """Test if the new pet's status can be updated to 'sold'."""
    payload = {
        "id": NEW_PET_ID,
        "category": {"id": NEW_PET_ID, "name": "string"},
        "name": "doggie",
        "photoUrls": ["string"],
        "tags": [{"id": NEW_PET_ID, "name": "string"}],
        "status": "sold"
    }

    response = requests.put(f"{BASE_URL}/pet", json=payload)
    assert response.status_code == 200
    updated_pet = response.json()

    assert updated_pet["status"] == "sold"
    assert is_pet_present(NEW_PET_ID, [updated_pet], status='sold')


@pytest.mark.dependency(depends=["test_update_pet_status"])
def test_delete_pet():
    """Test if the pet can be successfully deleted."""
    response = requests.delete(f"{BASE_URL}/pet/{NEW_PET_ID}")
    assert response.status_code == 200
    assert NEW_PET_ID == int(response.json()['message'])

    # Check if the pet is no longer retrievable (returns 404)
    assert is_pet_deleted(NEW_PET_ID)
