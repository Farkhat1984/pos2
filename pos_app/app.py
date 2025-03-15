# main.py
import os

import cv2
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from pos_app.components.customsnackbar import CustomSnackbar
from pos_app.core.api_client import ApiClient
from pos_app.core.auth_manager import AuthManager
from pos_app.core.database.database_manager import DatabaseManager
from pos_app.screens.scan_invoice_screen import ScanInvoiceScreen
import screens
from screens.invoice_edit_screen import InvoiceEditScreen
from screens.invoice_history_screen import InvoiceHistoryScreen
from screens.product_search_screen import ProductSearchScreen

# Установка размера окна для режима разработки
Window.size = (360, 640)


def load_kv_files(directory):
    """Загружает все .kv файлы из указанной директории"""
    for filename in os.listdir(directory):
        if filename.endswith('.kv'):
            kv_path = os.path.join(directory, filename)
            Builder.load_file(kv_path)
            print(f"Загружен KV-файл: {filename}")


class POSApp(MDApp):
    current_invoice = []
    temp_barcode = ""
    temp_name = ""
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

        kv_directory = os.path.join(os.path.dirname(__file__), 'kv')
        if os.path.exists(kv_directory):
            load_kv_files(kv_directory)
        # Переменные для камеры
        self.camera_instance = None
        self.camera_running = False
        self.barcode_scanner_thread = None

        return Builder.load_file('pos_app.kv')

    def on_start(self):
        self.root.transition.duration = 0.2

        self.root.add_widget(screens.LoginScreen(name='login'))
        self.root.add_widget(screens.MainScreen(name='main'))
        self.root.add_widget(ScanInvoiceScreen(name='scan_invoice'))
        self.root.add_widget(screens.InventoryScreen(name='inventory'))
        self.root.add_widget(screens.AnalyticsScreen(name='analytics'))
        self.root.add_widget(screens.ProductCreateScreen(name='product_create'))
        self.root.add_widget(screens.ProductEditScreen(name='product_edit'))

        # Добавляем новые экраны
        self.root.add_widget(InvoiceHistoryScreen(name='invoice_history'))
        self.root.add_widget(InvoiceEditScreen(name='invoice_edit'))
        self.root.add_widget(ProductSearchScreen(name='product_search'))

        # Добавьте в класс POSApp новые атрибуты:
        # editing_invoice_id - ID редактируемой накладной
        # scan_return_screen - название экрана, на который надо вернуться после сканирования

        self.editing_invoice_id = 0
        self.scan_return_screen = 'main'

        if self.auth.is_authenticated():
            self.api.set_auth_token(self.auth.token)
            self.root.current = 'main'  # Автоматический вход, если авторизован

    def open_product_edit(self, product):
        """Открыть экран редактирования товара"""
        if product:
            # Сохраняем ID товара для редактирования
            self.temp_product_id = product['id']
            # Переходим на экран редактирования товара
            self.root.current = 'product_edit'
        else:
            self.show_snackbar("Товар не найден", 1.5)
    # Обновить метод scan_product:
    def scan_product(self, barcode):
        """Обработка сканированного штрих-кода"""
        product = self.db.find_product_by_barcode(barcode)

        if product:
            if self.scan_for_invoice:
                # Теперь не переходим на экран invoice автоматически
                # Вместо этого возвращаем товар для обработки на текущей странице
                return product
            else:
                self.open_product_edit(product)
                return None
        else:
            return self.check_cloud_database(barcode)

    def login_success(self, token, user_data):
        """Вызывается после успешной авторизации пользователя"""
        self.api.set_auth_token(token)
        self.root.current = 'main'

    # Обновить метод check_cloud_database:
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
                # Возвращаем продукт вместо автоматического перехода
                return product
            else:
                self.open_product_edit(product)
                return None
        else:
            # Возвращаем None для показа диалога создания продукта
            return None

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

    # Обновить метод add_to_invoice:
    def add_to_invoice(self, product):
        """Добавить товар в накладную"""
        # Если товар с нулевой ценой (был получен из облака), предложить редактировать его
        if product['price'] == 0:
            return False  # Требуется указать цену

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
                self.current_invoice[i][int('total')] = self.current_invoice[i][int('quantity')] * \
                                                        self.current_invoice[i][
                                                            int('price')]
                return True

        self.current_invoice.append(item)
        return True

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
