# api_client.py
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
            self.headers["X-API-Key"] = token
        elif "X-API-Key" in self.headers:
            del self.headers["X-API-Key"]

    def get_product(self, barcode):
        """Получение информации о товаре по штрих-коду"""
        try:
            response = requests.get(
                f"{self.base_url}/products/by-barcode/{barcode}",
                headers=self.headers,
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                # Возвращаем только barcode и name
                return {
                    'barcode': data.get('barcode'),
                    'name': data.get('sku_name')
                }
            elif response.status_code == 404:
                return None
            elif response.status_code == 401:
                app = MDApp.get_running_app()
                if app:
                    app.show_snackbar(text="Ошибка авторизации. Пожалуйста, войдите снова.", duration=2)
                return None
            else:
                app = MDApp.get_running_app()
                if app:
                    app.show_snackbar(text=f"Ошибка API: {response.status_code}", duration=2)
                return None

        except requests.exceptions.RequestException as e:
            app = MDApp.get_running_app()
            if app:
                app.show_snackbar(text="Ошибка соединения с сервером", duration=2)
            return None