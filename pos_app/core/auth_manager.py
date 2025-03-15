# auth.py
import json
import logging
import os
import requests
from kivymd.app import MDApp

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("auth_manager")
class AuthManager:
    def __init__(self, api_url):
        """Инициализация менеджера авторизации"""
        self.api_url = api_url
        self.auth_file = "auth_data.json"
        self.token = None
        self.user_data = None
        self.load_auth_data()

    def login(self, username, password):
        """Авторизация пользователя"""
        logger.debug(f"Попытка входа пользователя: {username}")
        try:
            # Проверяем URL - обратите внимание на полный путь
            login_url = f"{self.api_url}/auth/token"
            logger.debug(f"URL для авторизации: {login_url}")

            # Данные для входа
            login_data = {
                "username": username,
                "password": password
            }

            # Заголовки запроса
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            # Выполнение запроса с явным указанием метода POST
            logger.debug(f"Отправка POST запроса к: {login_url}")
            logger.debug(f"Заголовки: {headers}")
            logger.debug(f"Данные: {json.dumps({**login_data, 'password': '*****'})}")

            # Важно: НЕ СЛЕДОВАТЬ перенаправлениям автоматически
            # Мы сами обработаем перенаправление, чтобы сохранить метод POST
            session = requests.Session()
            session.allow_redirects = False  # Отключаем автоматические перенаправления

            response = session.post(
                login_url,
                json=login_data,
                headers=headers,
                timeout=10
            )

            # Обработка перенаправления (если оно есть)
            if response.status_code in (301, 302, 303, 307, 308):
                redirect_url = response.headers.get('Location')
                logger.debug(f"Получено перенаправление на: {redirect_url}")

                # Выполняем запрос по новому URL, сохраняя метод POST
                response = session.post(
                    redirect_url,
                    json=login_data,
                    headers=headers,
                    timeout=10
                )

            logger.debug(f"Получен ответ с кодом: {response.status_code}")
            logger.debug(f"Заголовки ответа: {response.headers}")
            logger.debug(f"Тело ответа: {response.text}")

            # Проверяем успешность ответа (статус 200 OK)
            if response.status_code == 200:
                try:
                    # Парсим JSON ответ
                    response_data = response.json()

                    # ИСПРАВЛЕНО: Извлекаем access_token вместо token
                    self.token = response_data.get('access_token')  # Изменено с 'token' на 'access_token'
                    self.user_data = response_data.get('user')

                    # Добавляем отладочный вывод
                    logger.debug(f"Полученный токен: {self.token}")

                    # Сохраняем данные аутентификации
                    self.save_auth_data()

                    # Уведомляем приложение об успешном входе
                    app = MDApp.get_running_app()
                    if app:
                        app.login_success(self.token, self.user_data)
                    return True
                except json.JSONDecodeError:
                    logger.error("Ошибка при парсинге JSON ответа")
                    app = MDApp.get_running_app()
                    if app:
                        app.show_snackbar(text="Ошибка при обработке ответа сервера", duration=2)
                    return False
            else:
                error_message = f"Ошибка авторизации: {response.status_code}"
                logger.error(error_message)
                app = MDApp.get_running_app()
                if app:
                    app.show_snackbar(text=error_message, duration=2)
                return False

        except requests.exceptions.RequestException as e:
            app = MDApp.get_running_app()
            if app:
                app.show_snackbar(text=f"Ошибка соединения с сервером: {str(e)}", duration=2)
            return False

    def logout(self):
        """Выход из системы и удаление сохраненных данных"""
        self.token = None
        self.user_data = None
        if os.path.exists(self.auth_file):
            os.remove(self.auth_file)

    def is_authenticated(self):
        """Проверка, авторизован ли пользователь"""
        return self.token is not None

    def get_auth_header(self):
        """Получение заголовка авторизации для API запросов"""
        if self.token:
            return {"X-API-Key": self.token}
        return {}

    def save_auth_data(self):
        """Сохранение данных авторизации в файл"""
        auth_data = {
            "token": self.token,
            "user": self.user_data
        }
        try:
            with open(self.auth_file, 'w') as f:
                json.dump(auth_data, f)
        except Exception as e:
            app = MDApp.get_running_app()
            if app:
                app.show_snackbar(text=f"Ошибка сохранения данных авторизации: {str(e)}", duration=2)

    def load_auth_data(self):
        """Загрузка данных авторизации из файла"""
        if not os.path.exists(self.auth_file):
            return

        try:
            with open(self.auth_file, 'r') as f:
                auth_data = json.load(f)
                self.token = auth_data.get("token")
                self.user_data = auth_data.get("user")
        except Exception as e:
            app = MDApp.get_running_app()
            if app:
                app.show_snackbar(text=f"Ошибка загрузки данных авторизации: {str(e)}", duration=2)

    def get_user_info(self):
        """Получение информации о текущем пользователе"""
        return self.user_data