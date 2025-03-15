# main.py
import cv2
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.snackbar import MDSnackbar
from kivymd.uix.snackbar import MDSnackbar

from pos_app.components.customsnackbar import CustomSnackbar
from pos_app.core.api_client import ApiClient
from pos_app.core.auth_manager import AuthManager
from pos_app.core.database.database_manager import DatabaseManager

import screens

# Установка размера окна для режима разработки
Window.size = (360, 640)


class POSApp(MDApp):
    current_invoice = []
    temp_barcode = ""
    scan_for_invoice = True
    temp_product_id = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseManager()
        self.api = ApiClient("https://leema.kz")  # Укажите ваш URL API
        self.auth = AuthManager("https://leema.kz")

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.primary_hue = "500"
        self.theme_cls.accent_palette = "Amber"
        self.theme_cls.theme_style = "Light"

        # Проверка доступности OpenCV
        try:
            import cv2
            self.opencv_available = True
            print("OpenCV доступен, функциональность камеры включена")
        except ImportError:
            self.opencv_available = False
            print("OpenCV (cv2) недоступен. Установите opencv-python для функциональности камеры.")

        # Переменные для камеры
        self.camera_instance = None
        self.camera_running = False
        self.barcode_scanner_thread = None

        return Builder.load_file('pos_app.kv')
    def on_start(self):
        self.root.transition.duration = 0.2

        self.root.add_widget(screens.LoginScreen(name='login'))
        self.root.add_widget(screens.MainScreen(name='main'))
        self.root.add_widget(screens.ScanScreen(name='scan'))
        self.root.add_widget(screens.InvoiceScreen(name='invoice'))
        self.root.add_widget(screens.InventoryScreen(name='inventory'))
        self.root.add_widget(screens.AnalyticsScreen(name='analytics'))
        self.root.add_widget(screens.ProductCreateScreen(name='product_create'))
        self.root.add_widget(screens.ProductEditScreen(name='product_edit'))

        if self.auth.is_authenticated():
            self.api.set_auth_token(self.auth.token)
            self.root.current = 'main'  # Автоматический вход, если авторизован

    def login_success(self, token, user_data):
        """Вызывается после успешной авторизации пользователя"""
        self.api.set_auth_token(token)
        self.root.current = 'main'

    def scan_product(self, barcode):
        """Обработка сканированного штрих-кода"""
        product = self.db.find_product_by_barcode(barcode)

        if product:
            if self.scan_for_invoice:
                self.add_to_invoice(product)
            else:
                self.open_product_edit(product)
        else:
            self.check_cloud_database(barcode)

    def check_cloud_database(self, barcode):
        """Проверка товара в облачной базе"""
        cloud_product = self.api.get_product(barcode)

        if cloud_product:
            # Заполняем только штрих-код и название из облака
            product_id = self.db.add_product(
                barcode=cloud_product['barcode'],
                name=cloud_product['name'],
                price=0,  # Значения по умолчанию
                cost_price=0,
                quantity=0,
                unit='шт',
                group='',
                subgroup=''
            )
            product = self.db.find_product_by_id(product_id)

            if self.scan_for_invoice:
                self.add_to_invoice(product)
            else:
                self.open_product_edit(product)
        else:
            self.show_create_product_dialog(barcode)

    def show_create_product_dialog(self, barcode):
        """Диалог для создания нового товара"""
        self.temp_barcode = barcode
        dialog = MDDialog(
            title="Товар не найден",
            text="Товар не найден в базах данных. Создать новый?",
            buttons=[
                MDFlatButton(
                    text="ОТМЕНА",
                    on_release=lambda x: dialog.dismiss()
                ),
                MDFlatButton(
                    text="СОЗДАТЬ",
                    on_release=lambda x: self.open_create_product(dialog)
                ),
            ],
        )
        dialog.open()

    def open_create_product(self, dialog):
        """Открыть экран создания товара"""
        dialog.dismiss()
        self.root.current = 'product_create'

    def add_to_invoice(self, product):
        """Добавить товар в накладную"""
        # Если товар с нулевой ценой (был получен из облака), предложить редактировать его
        if product['price'] == 0:
            dialog = MDDialog(
                title="Требуется указать цену",
                text=f"Для товара '{product['name']}' не указана цена. Заполнить данные?",
                buttons=[
                    MDFlatButton(
                        text="ПОЗЖЕ",
                        on_release=lambda x: (dialog.dismiss(), self.root.current =='invoice')
                    ),
                    MDFlatButton(
                        text="ЗАПОЛНИТЬ",
                        on_release=lambda x: (dialog.dismiss(), self.open_product_edit(product))
                    ),
                ],
            )
            dialog.open()
            return

        item = {
            'product_id': product['id'],
            'barcode': product['barcode'],
            'name': product['name'],
            'price': product['price'],
            'quantity': 1,
            'total': product['price']
        }

        for i, existing_item in enumerate(self.current_invoice):
            if existing_item['product_id'] == item['product_id']:
                self.current_invoice[i][int('quantity')] += 1
                self.current_invoice[i][int('total')] = self.current_invoice[i][int('quantity')] * self.current_invoice[i][
                    int('price')]
                message = f"Добавлено: {product['name']} (x{self.current_invoice[i][int('quantity')]})"
                self.show_snackbar(message, 1.5)
                self.root.current = 'invoice'
                return

        self.current_invoice.append(item)
        message = f"Добавлено: {product['name']}"
        self.show_snackbar(message, 1.5)
        self.root.current = 'invoice'
    def open_product_edit(self, product):
        """Открыть экран редактирования товара"""
        self.temp_product_id = product['id']
        self.root.current = 'product_edit'

    def save_invoice(self):
        """Сохранить накладную"""
        if not self.current_invoice:
            self.show_snackbar("Накладная пуста!", 1.5)
            return

        total = sum(item['total'] for item in self.current_invoice)
        payment_status = "Оплачено"
        if total == 0:
            payment_status = "В долг"

        invoice_id = self.db.create_invoice(total, payment_status)

        for item in self.current_invoice:
            self.db.add_invoice_item(
                invoice_id,
                item['product_id'],
                item['quantity'],
                item['price'],
                item['total']
            )

            product = self.db.find_product_by_id(item['product_id'])
            new_quantity = product['quantity'] - item['quantity']
            if new_quantity < 0:
                new_quantity = 0
            self.db.update_product_quantity(item['product_id'], new_quantity)

        self.current_invoice = []
        self.show_snackbar(f"Накладная #{invoice_id} сохранена", 2)
        self.root.current = 'main'

    def on_stop(self):
        """При остановке приложения"""
        self.db.close()

    def show_snackbar(self, text, duration=1.5):
        """Удобный метод для показа уведомлений"""
        from kivymd.uix.label import MDLabel

        snackbar = CustomSnackbar(duration=duration)
        label = MDLabel(text=text, halign="center", theme_text_color="Custom", text_color=[1, 1, 1, 1])
        snackbar.add_widget(label)
        snackbar.open()
if __name__ == '__main__':
    POSApp().run()