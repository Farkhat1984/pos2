# screens/product_create_screen.py
from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp


class ProductCreateScreen(Screen):
    def on_enter(self):
        """Вызывается при переходе на экран"""
        app = MDApp.get_running_app()

        # Заполняем штрих-код и имя товара (если есть)
        self.ids.barcode_input.text = app.temp_barcode

        # Используем имя товара из temp_name, если оно задано
        if hasattr(app, 'temp_name') and app.temp_name:
            self.ids.name_input.text = app.temp_name
        else:
            self.ids.name_input.text = ""

        self.ids.price_input.text = ""
        self.ids.cost_price_input.text = ""
        self.ids.quantity_input.text = ""
        self.ids.unit_input.text = "шт"

        # Устанавливаем фокус на поле названия для удобства
        self.ids.name_input.focus = True

    def create_product(self):
        """Создание нового товара"""
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
        try:
            product_id = app.db.add_product(barcode, name, price, cost_price, quantity, unit)
            app = MDApp.get_running_app()
            if app:
                app.show_snackbar(text=f"Товар '{name}' успешно создан", duration=1.5)

            if app.scan_for_invoice:
                product = app.db.find_product_by_id(product_id)
                app.add_to_invoice(product)
            else:
                self.manager.current = 'inventory'

        except Exception as e:
            app = MDApp.get_running_app()
            if app:
                app.show_snackbar(text=f"Ошибка при создании товара: {str(e)}", duration=2)