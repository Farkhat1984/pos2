# api_client.py - с исправлением для X-API-Key
import requests
from kivymd.app import MDApp


class ApiClient:
    def __init__(self, base_url):
        """Инициализация API клиента"""
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.auth_token = None

    def set_auth_token(self, token):
        """Установка токена авторизации"""
        self.auth_token = token
        if token:
            # Используем X-API-Key для передачи токена, как в примере curl
            self.headers["X-API-Key"] = token
        elif "X-API-Key" in self.headers:
            del self.headers["X-API-Key"]

    def get_product(self, barcode):
        """Получение информации о товаре по штрих-коду"""
        try:
            # Добавляем логирование для проверки заголовков
            app = MDApp.get_running_app()
            if app:
                print(f"Запрос к API с заголовками: {self.headers}")

            response = requests.get(
                f"{self.base_url}/products/by-barcode/{barcode}",
                headers=self.headers,
                timeout=5
            )

            # Добавляем логирование для отладки
            print(f"Статус ответа: {response.status_code}")
            if response.status_code != 200:
                print(f"Тело ответа: {response.text}")

            if response.status_code == 200:
                data = response.json()
                # Возвращаем данные в соответствии с форматом API
                return {
                    'barcode': data.get('barcode'),
                    'name': data.get('sku_name')
                }
            elif response.status_code == 404:
                return None
            elif response.status_code == 401 or response.status_code == 403:
                app = MDApp.get_running_app()
                if app:
                    app.show_snackbar(text=f"Ошибка авторизации ({response.status_code}). Пожалуйста, войдите снова.",
                                      duration=2)
                return None
            else:
                app = MDApp.get_running_app()
                if app:
                    app.show_snackbar(text=f"Ошибка API: {response.status_code}", duration=2)
                return None

        except requests.exceptions.RequestException as e:
            app = MDApp.get_running_app()
            if app:
                app.show_snackbar(text=f"Ошибка соединения с сервером: {str(e)}", duration=2)
            return None