# screens/login_screen.py
from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp



class LoginScreen(Screen):
    def login(self):
        """Обработка входа в систему"""
        app = MDApp.get_running_app()
        username = self.ids.username_input.text.strip()
        password = self.ids.password_input.text

        if not username or not password:
            app.show_snackbar(text="Введите логин и пароль", duration=1.5)
            return

        # Отображение индикатора загрузки
        self.ids.login_button.disabled = True
        self.ids.loading_indicator.active = True

        try:
            # Попытка входа через API
            success = app.auth.login(username, password)

            if success:
                app.show_snackbar(text="Вход выполнен успешно", duration=1.5)
                app.login_success(app.auth.token, app.auth.user_data)  # Вызов обработчика успешного входа
                self.manager.current = 'main'
            else:
                # Ошибка отображается в AuthManager через show_snackbar
                pass
        except Exception as e:
            import traceback
            traceback.print_exc()
            app.show_snackbar(text=f"Ошибка входа: {str(e)}", duration=2)
        finally:
            # Скрытие индикатора загрузки
            self.ids.login_button.disabled = False
            self.ids.loading_indicator.active = False