# screens/scan_screen.py
from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp

from pos_app.components.customsnackbar import CustomSnackbar
from kivy.properties import BooleanProperty, ObjectProperty


class ScanScreen(Screen):
    current_barcode = ObjectProperty(None)
    scanning_active = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(ScanScreen, self).__init__(**kwargs)
        self.app = None
        self.camera_available = False

    def on_enter(self):
        """Вызывается при переходе на экран"""
        self.app = MDApp.get_running_app()

        # Безопасная проверка и установка текста в поле ввода
        if hasattr(self, 'ids') and 'barcode_input' in self.ids:
            self.ids.barcode_input.text = ""
            self.ids.barcode_input.focus = True

        # Отложим проверку камеры, чтобы kv-файл успел полностью загрузиться
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self.check_camera_availability(), 0.5)

    def on_leave(self):
        """Вызывается при уходе с экрана"""
        # Остановим сканирование, если оно активно
        if hasattr(self, 'scanning_active') and self.scanning_active:
            self.stop_scanning()

    def check_camera_availability(self, *args):
        """Проверка доступности камеры"""
        try:
            # Проверим, есть ли у приложения атрибут opencv_available
            if hasattr(self.app, 'opencv_available') and self.app.opencv_available:
                self.camera_available = True
                # Безопасно установим текст, проверив наличие элементов
                if hasattr(self, 'ids') and 'scan_info' in self.ids:
                    self.ids.scan_info.text = "Нажмите на иконку камеры для сканирования или введите штрих-код вручную"
            else:
                self.camera_available = False
                # Безопасно установим текст и состояние кнопки
                if hasattr(self, 'ids'):
                    if 'scan_info' in self.ids:
                        self.ids.scan_info.text = "Камера недоступна. Введите штрих-код вручную."
                    if 'camera_button' in self.ids:
                        self.ids.camera_button.disabled = True
                        self.ids.camera_button.opacity = 0.5
        except Exception as e:
            print(f"Ошибка при проверке доступности камеры: {e}")
            self.camera_available = False
            # Безопасно установим текст и состояние кнопки
            try:
                if hasattr(self, 'ids'):
                    if 'scan_info' in self.ids:
                        self.ids.scan_info.text = "Камера недоступна. Введите штрих-код вручную."
                    if 'camera_button' in self.ids:
                        self.ids.camera_button.disabled = True
                        self.ids.camera_button.opacity = 0.5
            except Exception as inner_e:
                print(f"Ошибка при обновлении UI: {inner_e}")

    def scan_barcode(self):
        """Обработка введенного штрих-кода"""
        # Безопасно получим текст из поля ввода
        barcode = ""
        if hasattr(self, 'ids') and 'barcode_input' in self.ids:
            barcode = self.ids.barcode_input.text.strip()

        if not barcode:
            self.show_snackbar("Введите штрих-код!")
            return

        # Показываем успешное сканирование
        self.show_snackbar("ОК", 1.0)

        # Передаем штрих-код в приложение для обработки
        self.app.scan_product(barcode)

    def show_snackbar(self, text, duration=1.5):
        """Показать уведомление пользователю"""
        snackbar = CustomSnackbar()
        snackbar.text = text
        snackbar.duration = duration
        snackbar.pos_hint = {"center_x": 0.5, "y": 0.1}
        snackbar.size_hint_x = 0.8
        snackbar.open()

    def stop_scanning(self):
        """Остановка сканирования"""
        if hasattr(self, 'scanning_active') and self.scanning_active:
            self.scanning_active = False
            # Дополнительная логика для остановки сканирования
            if self.app and hasattr(self.app, 'stop_camera'):
                self.app.stop_camera()