# screens/product_search_screen.py
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivymd.app import MDApp
from kivymd.uix.list import TwoLineIconListItem, IconLeftWidget
from pos_app.components.customsnackbar import CustomSnackbar


class ProductSearchScreen(Screen):
    search_query = StringProperty('')

    def on_enter(self):
        """Вызывается при переходе на экран"""
        self.app = MDApp.get_running_app()

        # Очищаем поле поиска
        if hasattr(self, 'ids') and 'search_input' in self.ids:
            self.ids.search_input.text = ''

        # Загружаем все товары по умолчанию
        self.search_products()

    def search_products(self):
        """Поиск товаров по введенному тексту"""
        if not hasattr(self, 'ids') or 'product_list' not in self.ids:
            return

        self.ids.product_list.clear_widgets()

        # Получаем текст поиска
        if hasattr(self, 'ids') and 'search_input' in self.ids:
            self.search_query = self.ids.search_input.text.strip()

        # Получаем список товаров
        products = []
        if self.search_query:
            products = self.app.db.search_products(self.search_query)
        else:
            products = self.app.db.get_all_products('name')

        if not products:
            item = TwoLineIconListItem(
                text="Товары не найдены",
                secondary_text="Измените поисковый запрос или добавьте новый товар"
            )
            self.ids.product_list.add_widget(item)
            return

        # Отображаем товары в списке
        for product in products:
            icon = IconLeftWidget(icon="package-variant")

            item = TwoLineIconListItem(
                text=f"{product['name']}",
                secondary_text=f"Цена: {product['price']:.2f} ₸ - Остаток: {product['quantity']} {product['unit']}",
                on_release=lambda x, p=product: self.add_to_invoice(p)
            )
            item.add_widget(icon)
            self.ids.product_list.add_widget(item)

    def add_to_invoice(self, product):
        """Добавление товара в редактируемую накладную"""
        # Проверяем наличие цены
        if product['price'] == 0:
            self.show_price_dialog(product)
            return

        # Создаем элемент для накладной
        item = {
            'product_id': product['id'],
            'barcode': product['barcode'],
            'name': product['name'],
            'price': product['price'],
            'quantity': 1,
            'total': product['price']
        }

        # Проверяем, есть ли уже такой товар в накладной
        for i, existing_item in enumerate(self.app.current_invoice):
            if existing_item['product_id'] == item['product_id']:
                self.app.current_invoice[i]['quantity'] += 1
                self.app.current_invoice[i]['total'] = self.app.current_invoice[i]['quantity'] * \
                                                       self.app.current_invoice[i]['price']
                message = f"Добавлено: {product['name']} (x{self.app.current_invoice[i]['quantity']})"
                self.show_snackbar(message, 1.5)
                # Возвращаемся к редактированию накладной
                self.manager.current = 'invoice_edit'
                return

        # Добавляем новый товар в накладную
        self.app.current_invoice.append(item)
        message = f"Добавлено: {product['name']}"
        self.show_snackbar(message, 1.5)
        # Возвращаемся к редактированию накладной
        self.manager.current = 'invoice_edit'

    def show_price_dialog(self, product):
        """Показать диалог о том, что товар имеет нулевую цену"""
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton

        dialog = MDDialog(
            title="Товар с нулевой ценой",
            text=f"Товар '{product['name']}' имеет нулевую цену. Сначала обновите цену товара.",
            buttons=[
                MDFlatButton(
                    text="ПОНЯТНО",
                    on_release=lambda x: dialog.dismiss()
                ),
            ],
        )
        dialog.open()

    def scan_barcode(self):
        """Переход к сканированию штрих-кода"""
        # Меняем флаг назначения сканирования для добавления в накладную
        self.app.scan_for_invoice = True
        self.app.scan_return_screen = 'invoice_edit'
        self.manager.current = 'scan_invoice'

    def show_snackbar(self, text, duration=1.5):
        """Показать уведомление пользователю"""
        snackbar = CustomSnackbar()
        snackbar.text = text
        snackbar.duration = duration
        snackbar.pos_hint = {"center_x": 0.5, "y": 0.1}
        snackbar.size_hint_x = 0.8
        snackbar.open()