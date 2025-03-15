# screens/invoice_screen.py
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, NumericProperty
from kivymd.app import MDApp
from kivymd.uix.list import OneLineIconListItem, TwoLineIconListItem, IconLeftWidget
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton

from pos_app.components.customsnackbar import CustomSnackbar



class InvoiceScreen(Screen):
    total_amount = NumericProperty(0)

    def on_enter(self):
        """Вызывается при переходе на экран"""
        self.update_invoice_items()

    def update_invoice_items(self):
        """Обновление списка товаров в накладной"""
        app = MDApp.get_running_app()
        self.ids.invoice_items.clear_widgets()
        self.total_amount = sum(item['total'] for item in app.current_invoice)
        self.ids.total_label.text = f"ИТОГО: {self.total_amount:.2f}"

        if not app.current_invoice:
            empty_item = OneLineIconListItem(
                text="Накладная пуста. Отсканируйте товар."
            )
            self.ids.invoice_items.add_widget(empty_item)
            return

        for item in app.current_invoice:
            icon = IconLeftWidget(icon="package-variant")
            list_item = TwoLineIconListItem(
                text=f"{item['name']}",
                secondary_text=f"{item['quantity']} x {item['price']:.2f} = {item['total']:.2f}",
                # Исправлено: используем i=item вместо item=self.item
                on_release=lambda x, i=item: self.edit_item(i)
            )
            list_item.add_widget(icon)
            self.ids.invoice_items.add_widget(list_item)

    def edit_item(self, item):
        """Редактирование товара в накладной"""
        app = MDApp.get_running_app()

        for i, invoice_item in enumerate(app.current_invoice):
            if invoice_item['product_id'] == item['product_id']:
                self.item_index = i
                break

        self.edit_dialog = MDDialog(
            title=f"Изменить: {item['name']}",
            type="custom",
            content_cls=InvoiceItemEdit(
                item_quantity=item['quantity'],
                item_price=item['price']
            ),
            buttons=[
                MDFlatButton(
                    text="ОТМЕНА",
                    on_release=lambda x: self.edit_dialog.dismiss()
                ),
                MDFlatButton(
                    text="УДАЛИТЬ",
                    theme_text_color="Error",
                    on_release=lambda x: self.remove_item()
                ),
                MDRaisedButton(
                    text="СОХРАНИТЬ",
                    on_release=lambda x: self.save_item_changes()
                ),
            ],
        )
        self.edit_dialog.open()

    def remove_item(self):
        """Удалить товар из накладной"""
        app = MDApp.get_running_app()
        if hasattr(self, 'item_index'):
            if 0 <= self.item_index < len(app.current_invoice):
                del app.current_invoice[self.item_index]
                self.edit_dialog.dismiss()
                self.update_invoice_items()
                self.show_snackbar("Товар удален из накладной")

    def save_item_changes(self):
        """Сохранить изменения товара в накладной"""
        app = MDApp.get_running_app()

        if hasattr(self, 'item_index') and hasattr(self.edit_dialog, 'content_cls'):
            new_quantity = self.edit_dialog.content_cls.item_quantity
            new_price = self.edit_dialog.content_cls.item_price

            if new_quantity <= 0:
                self.show_snackbar("Количество должно быть больше 0")
                return

            if new_price < 0:
                self.show_snackbar("Цена не может быть отрицательной")
                return

            app.current_invoice[self.item_index]['quantity'] = new_quantity
            app.current_invoice[self.item_index]['price'] = new_price
            app.current_invoice[self.item_index]['total'] = new_quantity * new_price

            self.edit_dialog.dismiss()
            self.update_invoice_items()
            self.show_snackbar("Товар обновлен")

    def save_invoice(self):
        """Сохранить накладную"""
        app = MDApp.get_running_app()
        app.save_invoice()

    def show_snackbar(self, text, duration=1.5):
        """Показать уведомление пользователю"""
        snackbar = CustomSnackbar()
        snackbar.text = text
        snackbar.duration = duration
        snackbar.pos_hint = {"center_x": 0.5, "y": 0.1}
        snackbar.size_hint_x = 0.8
        snackbar.open()


class InvoiceItemEdit(MDCard):
    item_quantity = NumericProperty(1)
    item_price = NumericProperty(0)

    def increment_quantity(self):
        self.item_quantity += 1

    def decrement_quantity(self):
        if self.item_quantity > 1:
            self.item_quantity -= 1