# screens/main_screen.py
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton


class MainScreen(Screen):
    user_name = StringProperty("")

    def on_enter(self):
        """Вызывается при переходе на экран"""
        app = MDApp.get_running_app()
        user_info = app.auth.get_user_info()
        if user_info:
            self.user_name = user_info.get("username", "Пользователь")

    def logout(self):
        """Выход из системы"""
        dialog = MDDialog(
            title="Выход из системы",
            text="Вы уверены, что хотите выйти?",
            buttons=[
                MDFlatButton(
                    text="ОТМЕНА",
                    on_release=lambda x: dialog.dismiss()
                ),
                MDRaisedButton(
                    text="ВЫЙТИ",
                    on_release=lambda x: self.confirm_logout(dialog)
                ),
            ],
        )
        dialog.open()

    def confirm_logout(self, dialog):
        """Подтверждение выхода из системы"""
        dialog.dismiss()
        app = MDApp.get_running_app()
        app.auth.logout()
        self.manager.current = 'login'