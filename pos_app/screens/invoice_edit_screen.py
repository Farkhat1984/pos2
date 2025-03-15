# screens/invoice_edit_screen.py
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, NumericProperty
from kivymd.app import MDApp
from kivymd.uix.list import OneLineIconListItem, TwoLineIconListItem, IconLeftWidget
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from pos_app.components.customsnackbar import CustomSnackbar


class InvoiceEditScreen(Screen):
    total_amount = NumericProperty(0)
    invoice_id = NumericProperty(0)

    def on_enter(self):
        """Вызывается при переходе на экран"""
        self.app = MDApp.get_running_app()

        # Получаем ID редактируемой накладной
        self.invoice_id = getattr(self.app, 'editing_invoice_id', 0)

        # Обновляем заголовок
        if hasattr(self, 'ids') and 'screen_title' in self.ids:
            self.ids.screen_title.title = f"Редактирование накладной #{self.invoice_id}"

        # Обновляем список товаров в накладной
        self.update_invoice_items()

    def update_invoice_items(self):
        """Обновление списка товаров в накладной"""
        if not hasattr(self, 'ids') or 'invoice_items' not in self.ids:
            return

        self.ids.invoice_items.clear_widgets()
        self.total_amount = sum(item['total'] for item in self.app.current_invoice)
        self.ids.total_label.text = f"ИТОГО: {self.total_amount:.2f}"

        if not self.app.current_invoice:
            empty_item = OneLineIconListItem(
                text="Накладная пуста. Добавьте товары или удалите накладную."
            )
            self.ids.invoice_items.add_widget(empty_item)
            return

        for item in self.app.current_invoice:
            icon = IconLeftWidget(icon="package-variant")
            list_item = TwoLineIconListItem(
                text=f"{item['name']}",
                secondary_text=f"{item['quantity']} x {item['price']:.2f} = {item['total']:.2f}",
                on_release=lambda x, i=item: self.edit_item(i)
            )
            list_item.add_widget(icon)
            self.ids.invoice_items.add_widget(list_item)

    def edit_item(self, item):
        """Редактирование товара в накладной"""
        for i, invoice_item in enumerate(self.app.current_invoice):
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
        if hasattr(self, 'item_index'):
            if 0 <= self.item_index < len(self.app.current_invoice):
                del self.app.current_invoice[self.item_index]
                self.edit_dialog.dismiss()
                self.update_invoice_items()
                self.show_snackbar("Товар удален из накладной")

    def save_item_changes(self):
        """Сохранить изменения товара в накладной"""
        if hasattr(self, 'item_index') and hasattr(self.edit_dialog, 'content_cls'):
            new_quantity = self.edit_dialog.content_cls.item_quantity
            new_price = self.edit_dialog.content_cls.item_price

            if new_quantity <= 0:
                self.show_snackbar("Количество должно быть больше 0")
                return

            if new_price < 0:
                self.show_snackbar("Цена не может быть отрицательной")
                return

            self.app.current_invoice[self.item_index]['quantity'] = new_quantity
            self.app.current_invoice[self.item_index]['price'] = new_price
            self.app.current_invoice[self.item_index]['total'] = new_quantity * new_price

            self.edit_dialog.dismiss()
            self.update_invoice_items()
            self.show_snackbar("Товар обновлен")

    def add_product(self):
        """Переход на экран добавления товаров"""
        self.manager.current = 'product_search'

    def save_changes(self):
        """Сохранить изменения в накладной"""
        if not self.app.current_invoice:
            self.show_snackbar("Накладная пуста! Нельзя сохранить пустую накладную.", 2)
            return

        # Вычисляем общую сумму
        total = sum(item['total'] for item in self.app.current_invoice)

        # По умолчанию статус "Оплачено"
        payment_status = "Оплачено"
        if total == 0:
            payment_status = "В долг"

        try:
            # Обновляем информацию о накладной
            self.app.db.cursor.execute(
                "UPDATE invoices SET total = ?, payment_status = ? WHERE id = ?",
                (total, payment_status, self.invoice_id)
            )

            # Удаляем старые позиции
            self.app.db.cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (self.invoice_id,))

            # Добавляем новые позиции
            for item in self.app.current_invoice:
                self.app.db.add_invoice_item(
                    self.invoice_id,
                    item['product_id'],
                    item['quantity'],
                    item['price'],
                    item['total']
                )

                # Обновляем остаток товара
                product = self.app.db.find_product_by_id(item['product_id'])
                # В данном случае мы не меняем остаток, так как это редактирование
                # А не новая продажа

            self.app.db.conn.commit()
            self.show_snackbar(f"Накладная #{self.invoice_id} обновлена", 2)

            # Очищаем текущую накладную и возвращаемся в историю
            self.app.current_invoice = []
            self.app.editing_invoice_id = 0
            self.manager.current = 'invoice_history'

        except Exception as e:
            self.show_snackbar(f"Ошибка сохранения накладной: {str(e)}", 3)

    def cancel_edit(self):
        """Отмена редактирования накладной"""
        # Запрашиваем подтверждение, если были внесены изменения
        self.confirm_dialog = MDDialog(
            title="Отменить изменения?",
            text="Все несохраненные изменения будут потеряны.",
            buttons=[
                MDFlatButton(
                    text="ОТМЕНА",
                    on_release=lambda x: self.confirm_dialog.dismiss()
                ),
                MDRaisedButton(
                    text="ВЫЙТИ БЕЗ СОХРАНЕНИЯ",
                    on_release=lambda x: self.exit_without_saving()
                ),
            ],
        )
        self.confirm_dialog.open()

    def exit_without_saving(self):
        """Выход без сохранения изменений"""
        if hasattr(self, 'confirm_dialog') and self.confirm_dialog:
            self.confirm_dialog.dismiss()

        # Очищаем текущую накладную и возвращаемся в историю
        self.app.current_invoice = []
        self.app.editing_invoice_id = 0
        self.manager.current = 'invoice_history'

    def show_snackbar(self, text, duration=1.5):
        """Показать уведомление пользователю"""
        snackbar = CustomSnackbar()
        snackbar.text = text
        snackbar.duration = duration
        snackbar.pos_hint = {"center_x": 0.5, "y": 0.1}
        snackbar.size_hint_x = 0.8
        snackbar.open()


# Используем тот же класс для редактирования товаров, что и в InvoiceScreen
class InvoiceItemEdit(MDCard):
    item_quantity = NumericProperty(1)
    item_price = NumericProperty(0)

    def increment_quantity(self):
        self.item_quantity += 1

    def decrement_quantity(self):
        if self.item_quantity > 1:
            self.item_quantity -= 1