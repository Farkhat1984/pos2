# screens/product_edit_screen.py
from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp



class ProductEditScreen(Screen):
    def on_enter(self):
        """Вызывается при переходе на экран"""
        app = MDApp.get_running_app()
        product = app.db.find_product_by_id(app.temp_product_id)

        if not product:
            app = MDApp.get_running_app()
            if app:
                app.show_snackbar(text="Товар не найден", duration=1.5)
            self.manager.current = 'inventory'
            return

        self.ids.product_title.text = product['name']
        self.ids.barcode_input.text = product['barcode']
        self.ids.name_input.text = product['name']
        self.ids.price_input.text = str(product['price'])
        self.ids.cost_price_input.text = str(product['cost_price'])
        self.ids.quantity_input.text = str(product['quantity'])

        if hasattr(self.ids, 'unit_input'):
            self.ids.unit_input.text = product.get('unit', 'шт')

    def update_product(self):
        """Обновление информации о товаре"""
        barcode = self.ids.barcode_input.text.strip()
        name = self.ids.name_input.text.strip()
        price_text = self.ids.price_input.text.strip()
        cost_price_text = self.ids.cost_price_input.text.strip()
        quantity_text = self.ids.quantity_input.text.strip()
        unit = self.ids.unit_input.text.strip() if hasattr(self.ids, 'unit_input') else "шт"

        if not barcode or not name:
            app = MDApp.get_running_app()
            if app:
                app.show_snackbar(text="Штрих-код и название обязательны", duration=1.5)
            return

        try:
            price = float(price_text) if price_text else 0
            cost_price = float(cost_price_text) if cost_price_text else 0
            quantity = int(quantity_text) if quantity_text else 0

            if price < 0 or cost_price < 0 or quantity < 0:
                app = MDApp.get_running_app()
                if app:
                    app.show_snackbar(text="Значения не могут быть отрицательными", duration=1.5)
                return

        except ValueError:
            app = MDApp.get_running_app()
            if app:
                app.show_snackbar(text="Введите корректные числовые значения", duration=1.5)
            return

        app = MDApp.get_running_app()
        success = app.db.update_product(app.temp_product_id, name, price, cost_price, quantity, unit)

        if success:
            app = MDApp.get_running_app()
            if app:
                app.show_snackbar(text=f"Товар '{name}' успешно обновлен", duration=1.5)
            self.manager.current = 'inventory'
        else:
            app = MDApp.get_running_app()
            if app:
                app.show_snackbar(text="Ошибка при обновлении товара", duration=1.5)