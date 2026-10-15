import uuid
import random

import requests


class BaseRequest:

    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")

    def _request(self, method, endpoint, body=None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = requests.request(
            method, url, json=body, headers={"Accept": "application/json"},
            timeout=20,
        )
        print(f"\n{method} {url}")
        print(f"Статус: {response.status_code}")
        print(f"Ответ: {response.text}")
        return response

    def get(self, endpoint):
        return self._request("GET", endpoint)

    def post(self, endpoint, body):
        return self._request("POST", endpoint, body)

    def put(self, endpoint, body):
        return self._request("PUT", endpoint, body)

    def delete(self, endpoint):
        return self._request("DELETE", endpoint)


def check_status(response, expected=200):
    assert response.status_code == expected, (
        f"Ожидался статус {expected}, получен {response.status_code}: "
        f"{response.text}"
    )


def test_user(api):
    username = f"student_{uuid.uuid4().hex[:12]}"
    user = {
        "id": int(uuid.uuid4().hex[:10], 16),
        "username": username,
        "firstName": "Ivan",
        "lastName": "Ivanov",
        "email": f"{username}@example.com",
        "password": "study_password_123",
        "phone": "1234567890",
        "userStatus": 0,
    }

    # POST /user
    response = api.post("user", user)
    check_status(response)
    assert response.json()["code"] == 200
    print("PASS: создание пользователя")

    try:
        # GET /user/{username}
        response = api.get(f"user/{username}")
        check_status(response)
        actual = response.json()
        for field in ("id", "username", "firstName", "email"):
            assert actual[field] == user[field], f"Не совпало поле {field}"
        print("PASS: получение пользователя")

        # PUT /user/{username}
        updated_user = {**user, "firstName": "Petr"}
        response = api.put(f"user/{username}", updated_user)
        check_status(response)
        assert response.json()["code"] == 200
        print("PASS: запрос обновления пользователя")

        # GET проверяет что обновление сохранилосб
        response = api.get(f"user/{username}")
        check_status(response)
        assert response.json()["firstName"] == "Petr"
        print("PASS: новое имя сохранено")
    finally:
        # DELETE /user/{username}
        response = api.delete(f"user/{username}")
        check_status(response)
        assert response.json()["message"] == username
        print("PASS: удаление пользователя")

    # GET проверка удаения
    response = api.get(f"user/{username}")
    check_status(response, 404)
    print("PASS: удалённый пользователь не найден")


def test_store(api):
    # GET /store/inventory
    response = api.get("store/inventory")
    check_status(response)
    inventory = response.json()
    assert isinstance(inventory, dict), "Ожидался объект с остатками"
    assert all(type(value) is int and value >= 0 for value in inventory.values())
    print("PASS: получение остатков")

    # swagger задает диапазон 1–10 для получения заказа
    order = {
        "id": random.randint(1, 10),
        "petId": 1,
        "quantity": 1,
        "shipDate": "2026-10-14T12:00:00.000Z",
        "status": "placed",
        "complete": False,
    }

    # POST /store/order
    response = api.post("store/order", order)
    check_status(response)
    created = response.json()
    assert created["id"] == order["id"]
    assert created["status"] == "placed"
    print("PASS: создание заказа")

    try:
        #GET /store/order/{orderId}
        response = api.get(f"store/order/{order['id']}")
        check_status(response)
        actual = response.json()
        for field in ("id", "petId", "quantity", "status", "complete"):
            assert actual[field] == order[field], f"Не совпало поле {field}"
        print("PASS: получение заказа")
    finally:
        # DELETE /store/order/{orderId}
        response = api.delete(f"store/order/{order['id']}")
        check_status(response)
        assert response.json()["message"] == str(order["id"])
        print("PASS: удаление заказа")

    # GET проверяем удаление
    response = api.get(f"store/order/{order['id']}")
    check_status(response, 404)
    print("PASS: удалённый заказ не найден")


if __name__ == "__main__":
    api = BaseRequest("https://petstore.swagger.io/v2")
    test_user(api)
    test_store(api)
    print("\nВсе проверки пройдены.")