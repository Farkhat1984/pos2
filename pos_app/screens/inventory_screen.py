# screens/inventory_screen.py
from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp
from kivymd.uix.snackbar import MDSnackbar
from kivymd.uix.list import OneLineIconListItem, TwoLineIconListItem, IconLeftWidget

from pos_app.components.customsnackbar import CustomSnackbar



class InventoryScreen(Screen):
    def on_enter(self):
        """Вызывается при переходе на экран"""
        self.update_inventory_list()

    def update_inventory_list(self):
        """Обновление списка товаров на складе"""
        app = MDApp.get_running_app()
        self.ids.inventory_list.clear_widgets()
        products = app.db.get_all_products()

        if not products:
            empty_item = OneLineIconListItem(
                text="Нет товаров на складе. Добавьте товары."
            )
            self.ids.inventory_list.add_widget(empty_item)
            return

        for product in products:
            # Выбираем иконку в зависимости от заполненности данных товара
            icon_name = "package-variant"
            if product['price'] == 0:
                icon_name = "package-variant-closed-alert"  # Используем другую иконку для товаров без цены

            icon = IconLeftWidget(icon=icon_name)

            # Формируем вторую строку с учетом нулевых значений
            secondary_text = f"Количество: {product['quantity']}"
            if product['price'] > 0:
                secondary_text += f", Цена: {product['price']:.2f}"
            else:
                secondary_text += ", Цена: не указана"

            list_item = TwoLineIconListItem(
                text=f"{product['name']}",
                secondary_text=secondary_text,
                on_release=lambda x, p=product: self.edit_product(p)
            )
            list_item.add_widget(icon)
            self.ids.inventory_list.add_widget(list_item)
    def edit_product(self, product):
        """Открыть экран редактирования товара"""
        app = MDApp.get_running_app()
        app.temp_product_id = product['id']
        self.manager.current = 'product_edit'

    def scan_for_inventory(self):
        """Сканировать товар для добавления в инвентарь"""
        app = MDApp.get_running_app()
        app.scan_for_invoice = False
        self.manager.current = 'product_create'

    def search_products(self):
        """Поиск товаров"""
        search_text = self.ids.search_input.text.strip()

        if not search_text:
            self.update_inventory_list()
            return

        app = MDApp.get_running_app()
        products = app.db.search_products(search_text)

        self.ids.inventory_list.clear_widgets()

        if not products:
            empty_item = OneLineIconListItem(
                text=f"Поиск по '{search_text}' не дал результатов."
            )
            self.ids.inventory_list.add_widget(empty_item)
            return

        for product in products:
            icon = IconLeftWidget(icon="package-variant")
            list_item = TwoLineIconListItem(
                text=f"{product['name']}",
                secondary_text=f"Количество: {product['quantity']}, Цена: {product['price']:.2f}",
                on_release=lambda x, p=product: self.edit_product(p)
            )
            list_item.add_widget(icon)
            self.ids.inventory_list.add_widget(list_item)

    def show_snackbar(self, text, duration=1.5):
        """Показать уведомление пользователю"""
        snackbar = CustomSnackbar()
        snackbar.text = text
        snackbar.duration = duration
        snackbar.pos_hint = {"center_x": 0.5, "y": 0.1}
        snackbar.size_hint_x = 0.8
        snackbar.open()