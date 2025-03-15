# screens/invoice_history_screen.py
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, NumericProperty, ListProperty
from kivymd.app import MDApp
from kivymd.uix.list import TwoLineIconListItem, IconLeftWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.pickers import MDDatePicker
from kivymd.uix.snackbar import MDSnackbar
from datetime import datetime, timedelta
import sqlite3
from pos_app.components.customsnackbar import CustomSnackbar


class InvoiceHistoryScreen(Screen):
    start_date = StringProperty('')
    end_date = StringProperty('')
    search_query = StringProperty('')
    invoices = ListProperty([])

    def __init__(self, **kwargs):
        super(InvoiceHistoryScreen, self).__init__(**kwargs)
        self.app = None
        self.dialog = None
        # По умолчанию устанавливаем период последних 30 дней
        today = datetime.now()
        self.end_date = today.strftime("%Y-%m-%d 23:59:59")
        self.start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d 00:00:00")

    def on_enter(self):
        """Вызывается при переходе на экран"""
        self.app = MDApp.get_running_app()

        # Показываем даты в полях
        self.update_date_labels()

        # Загружаем накладные
        self.load_invoices()

    def update_date_labels(self):
        """Обновление отображения дат на экране"""
        if hasattr(self, 'ids') and 'start_date_label' in self.ids and 'end_date_label' in self.ids:
            # Форматируем даты для отображения
            start = datetime.strptime(self.start_date, "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y")
            end = datetime.strptime(self.end_date, "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y")

            self.ids.start_date_label.text = start
            self.ids.end_date_label.text = end

    def load_invoices(self):
        """Загрузка списка накладных из базы данных"""
        if not hasattr(self, 'ids') or 'invoice_list' not in self.ids:
            return

        # Очищаем список
        self.ids.invoice_list.clear_widgets()

        try:
            # Получаем накладные из базы данных с учетом фильтра
            self.invoices = self.filter_invoices()

            if not self.invoices:
                # Если накладных нет, показываем сообщение
                item = TwoLineIconListItem(
                    text="Накладные не найдены",
                    secondary_text="Измените параметры поиска или создайте новую накладную"
                )
                self.ids.invoice_list.add_widget(item)
                return

            # Отображаем накладные в списке
            for invoice in self.invoices:
                icon = IconLeftWidget(icon="file-document-outline")

                # Форматируем дату и сумму для отображения
                invoice_date = datetime.strptime(invoice['date'], "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y %H:%M")

                # Преобразуем статус оплаты из целого числа в булево значение
                is_paid = bool(invoice['payment_status'])
                status_text = "Оплачено" if is_paid else "Не оплачено"

                # Создаем элемент списка
                item = TwoLineIconListItem(
                    text=f"Накладная #{invoice['id']}",
                    secondary_text=f"{invoice_date} - {invoice['total']:.2f} ₸ - {status_text}",
                    on_release=lambda x, inv=invoice: self.show_invoice_options(inv)
                )

                # Добавляем цветовое оформление в зависимости от статуса оплаты
                if is_paid:
                    # Зеленый для оплаченных накладных
                    item.bg_color = (0.7, 0.9, 0.7, 0.2)  # Светло-зеленый фон
                else:
                    # Красный для неоплаченных накладных
                    item.bg_color = (0.9, 0.7, 0.7, 0.2)  # Светло-красный фон

                item.add_widget(icon)
                self.ids.invoice_list.add_widget(item)

        except Exception as e:
            self.show_snackbar(f"Ошибка загрузки накладных: {str(e)}")

    def filter_invoices(self):
        """Фильтрация накладных по дате и поисковому запросу"""
        query = """
        SELECT i.*, COUNT(ii.id) as items_count 
        FROM invoices i
        LEFT JOIN invoice_items ii ON i.id = ii.invoice_id
        WHERE i.date BETWEEN ? AND ?
        """

        params = [self.start_date, self.end_date]

        # Добавляем поиск по номеру
        if self.search_query:
            # Для поиска по статусу оплаты преобразуем текст в число
            if self.search_query.lower() in ["оплачено", "оплачен", "paid"]:
                query += " AND i.payment_status = 1"
            elif self.search_query.lower() in ["не оплачено", "не оплачен", "unpaid"]:
                query += " AND i.payment_status = 0"
            else:
                # Поиск по номеру накладной
                search_term = f"%{self.search_query}%"
                query += " AND i.id LIKE ?"
                params.append(search_term)

        query += " GROUP BY i.id ORDER BY i.date DESC"

        # Выполняем запрос к БД
        self.app.db.cursor.execute(query, params)
        return self.app.db.cursor.fetchall()

    def search_invoices(self):
        """Поиск накладных по введенному тексту"""
        if hasattr(self, 'ids') and 'search_input' in self.ids:
            self.search_query = self.ids.search_input.text.strip()
            self.load_invoices()

    def show_invoice_options(self, invoice):
        """Отображение диалога с опциями для накладной"""
        if self.dialog:
            self.dialog.dismiss()

        # Преобразуем статус оплаты из целого числа в булево значение
        is_paid = bool(invoice['payment_status'])
        status_text = "Оплачено" if is_paid else "Не оплачено"

        self.dialog = MDDialog(
            title=f"Накладная #{invoice['id']}",
            text=f"Дата: {datetime.strptime(invoice['date'], '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y %H:%M')}\nСумма: {invoice['total']:.2f} ₸\nСтатус: {status_text}",
            buttons=[
                MDFlatButton(
                    text="ЗАКРЫТЬ",
                    on_release=lambda x: self.dialog.dismiss()
                ),
                MDFlatButton(
                    text="УДАЛИТЬ",
                    theme_text_color="Error",
                    on_release=lambda x: self.confirm_delete_invoice(invoice)
                ),
                MDRaisedButton(
                    text="РЕДАКТ.",
                    on_release=lambda x: self.edit_invoice(invoice)
                ),
            ],
        )
        self.dialog.open()

    def confirm_delete_invoice(self, invoice):
        """Подтверждение удаления накладной"""
        if self.dialog:
            self.dialog.dismiss()

        self.dialog = MDDialog(
            title="Подтверждение удаления",
            text=f"Вы уверены, что хотите удалить накладную #{invoice['id']}?\nЭто действие нельзя отменить.",
            buttons=[
                MDFlatButton(
                    text="ОТМЕНА",
                    on_release=lambda x: self.dialog.dismiss()
                ),
                MDRaisedButton(
                    text="УДАЛИТЬ",
                    theme_text_color="Error",
                    on_release=lambda x: self.delete_invoice(invoice)
                ),
            ],
        )
        self.dialog.open()

    def delete_invoice(self, invoice):
        """Удаление накладной из базы данных"""
        try:
            # Удаляем накладную из БД
            self.app.db.cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice['id'],))
            self.app.db.conn.commit()

            if self.dialog:
                self.dialog.dismiss()

            self.show_snackbar(f"Накладная #{invoice['id']} удалена")
            self.load_invoices()  # Обновляем список

        except Exception as e:
            self.show_snackbar(f"Ошибка удаления накладной: {str(e)}")

    def edit_invoice(self, invoice):
        """Открытие экрана редактирования накладной"""
        if self.dialog:
            self.dialog.dismiss()

        # Загружаем данные накладной в приложение
        self.load_invoice_for_edit(invoice['id'])

        # Переходим на экран редактирования
        self.manager.current = 'invoice_edit'

    def load_invoice_for_edit(self, invoice_id):
        """Загрузка данных накладной для редактирования"""
        # Получаем информацию о накладной
        invoice = self.app.db.get_invoice(invoice_id)

        # Сохраняем статус оплаты
        self.app.invoice_payment_status = bool(invoice.get('payment_status', 1))

        # Получаем все товары из накладной
        items = self.app.db.get_invoice_items(invoice_id)

        # Очищаем текущую накладную в памяти приложения
        self.app.current_invoice = []

        # Загружаем товары из накладной в текущую накладную
        for item in items:
            invoice_item = {
                'product_id': item['product_id'],
                'barcode': item['barcode'],
                'name': item['name'],
                'price': item['price'],
                'quantity': item['quantity'],
                'total': item['total']
            }
            self.app.current_invoice.append(invoice_item)

        # Сохраняем ID редактируемой накладной
        self.app.editing_invoice_id = invoice_id

    def show_date_picker(self, date_type):
        """Отображение диалога выбора даты"""
        if date_type == 'start':
            date_obj = datetime.strptime(self.start_date, "%Y-%m-%d %H:%M:%S")
        else:
            date_obj = datetime.strptime(self.end_date, "%Y-%m-%d %H:%M:%S")

        date_dialog = MDDatePicker(
            year=date_obj.year,
            month=date_obj.month,
            day=date_obj.day
        )
        date_dialog.bind(on_save=lambda instance, value, date_range: self.on_date_select(value, date_type))
        date_dialog.open()

    def on_date_select(self, date, date_type):
        """Обработка выбора даты"""
        selected_date = date.strftime("%Y-%m-%d")
        if date_type == 'start':
            self.start_date = f"{selected_date} 00:00:00"
        else:
            self.end_date = f"{selected_date} 23:59:59"

        self.update_date_labels()
        self.load_invoices()



    def show_snackbar(self, text, duration=1.5):
        """Показать уведомление пользователю"""
        snackbar = CustomSnackbar()
        snackbar.text = text
        snackbar.duration = duration
        snackbar.pos_hint = {"center_x": 0.5, "y": 0.1}
        snackbar.size_hint_x = 0.8
        snackbar.open()