# screens/scan_invoice_screen.py
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ObjectProperty
from kivymd.app import MDApp
from kivymd.uix.list import OneLineIconListItem, TwoLineIconListItem, IconLeftWidget
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.label import MDLabel
from pos_app.components.customsnackbar import CustomSnackbar
from kivy.clock import Clock


class ScanInvoiceScreen(Screen):
    """Объединенный экран сканирования и накладной"""
    total_amount = NumericProperty(0)
    current_barcode = ObjectProperty(None)
    scanning_active = BooleanProperty(False)
    payment_status = BooleanProperty(True)  # True = Оплачено, False = Не оплачено

    def __init__(self, **kwargs):
        super(ScanInvoiceScreen, self).__init__(**kwargs)
        self.app = None
        self.camera_available = False

    def on_enter(self):
        """Вызывается при переходе на экран"""
        self.app = MDApp.get_running_app()

        # Инициализация поля штрих-кода
        if hasattr(self, 'ids') and 'barcode_input' in self.ids:
            self.ids.barcode_input.text = ""
            self.ids.barcode_input.focus = True

        # Отложим проверку камеры
        Clock.schedule_once(lambda dt: self.check_camera_availability(), 0.5)

        # Установка статуса оплаты по умолчанию
        self.payment_status = True

        # Обновление списка товаров в накладной и кнопки итого
        self.update_invoice_items()

    def on_leave(self):
        """Вызывается при уходе с экрана"""
        if hasattr(self, 'scanning_active') and self.scanning_active:
            self.stop_scanning()

    def check_camera_availability(self, *args):
        """Проверка доступности камеры"""
        try:
            if hasattr(self.app, 'opencv_available') and self.app.opencv_available:
                self.camera_available = True
                if hasattr(self, 'ids') and 'scan_info' in self.ids:
                    self.ids.scan_info.text = "Сканируйте товар или введите штрих-код вручную"
            else:
                self.camera_available = False
                if hasattr(self, 'ids'):
                    if 'scan_info' in self.ids:
                        self.ids.scan_info.text = "Камера недоступна. Введите штрих-код вручную."
                    if 'camera_button' in self.ids:
                        self.ids.camera_button.disabled = True
                        self.ids.camera_button.opacity = 0.5
        except Exception as e:
            print(f"Ошибка при проверке доступности камеры: {e}")
            self.camera_available = False
            try:
                if hasattr(self, 'ids'):
                    if 'scan_info' in self.ids:
                        self.ids.scan_info.text = "Камера недоступна. Введите штрих-код вручную."
                    if 'camera_button' in self.ids:
                        self.ids.camera_button.disabled = True
                        self.ids.camera_button.opacity = 0.5
            except Exception as inner_e:
                print(f"Ошибка при обновлении UI: {inner_e}")

    def toggle_payment_status(self):
        """Переключение статуса оплаты при нажатии на кнопку ИТОГО"""
        self.payment_status = not self.payment_status

        # Обновляем цвет кнопки
        if hasattr(self, 'ids') and 'total_button' in self.ids:
            if self.payment_status:
                # Зеленый для статуса "Оплачено"
                self.ids.total_button.md_bg_color = (0.2, 0.7, 0.2, 1)
                self.show_snackbar("Статус: Оплачено")
            else:
                # Красный для статуса "Не оплачено"
                self.ids.total_button.md_bg_color = (0.7, 0.2, 0.2, 1)
                self.show_snackbar("Статус: Не оплачено")

    def scan_barcode(self):
        """Обработка введенного штрих-кода"""
        barcode = ""
        if hasattr(self, 'ids') and 'barcode_input' in self.ids:
            barcode = self.ids.barcode_input.text.strip()

        if not barcode:
            self.show_snackbar("Введите штрих-код!")
            return

        # Показываем успешное сканирование
        self.show_snackbar("Штрих-код обрабатывается...", 1.0)

        # Передаем штрих-код в приложение для обработки
        # Важно: теперь вместо переключения экрана, товар сразу добавится в накладную
        # на этой же странице
        self.app.scan_for_invoice = True
        self.process_product(barcode)

        # Очищаем поле ввода для следующего сканирования
        if hasattr(self, 'ids') and 'barcode_input' in self.ids:
            self.ids.barcode_input.text = ""
            self.ids.barcode_input.focus = True

    def process_product(self, barcode):
        """Обработка штрих-кода и добавление товара в накладную"""
        product = self.app.db.find_product_by_barcode(barcode)

        if product:
            self.add_to_invoice(product)
        else:
            # Проверка в облачной базе
            self.check_cloud_database(barcode)

    def check_cloud_database(self, barcode):
        """Проверка товара в облачной базе"""
        try:
            cloud_product = self.app.api.get_product(barcode)

            # Добавляем отладочный вывод для проверки формата ответа
            print(f"Ответ API: {cloud_product}")

            if cloud_product and isinstance(cloud_product, dict):
                # Сохраняем название из облака для экрана создания товара
                self.app.temp_name = cloud_product.get('name', f"Товар {barcode}")

                # Проверяем наличие ключей и добавляем товар в локальную базу
                product_id = self.app.db.add_product(
                    barcode=cloud_product.get('barcode', barcode),
                    name=self.app.temp_name,  # Используем сохраненное имя
                    price=0,  # Значения по умолчанию
                    cost_price=0,
                    quantity=0,
                    unit='шт',
                    group='',
                    subgroup=''
                )

                if product_id:
                    product = self.app.db.find_product_by_id(product_id)
                    if product:
                        self.add_to_invoice(product)
                    else:
                        self.show_snackbar(f"Ошибка при поиске созданного товара с ID {product_id}")
                        self.show_create_product_dialog(barcode)
                else:
                    self.show_snackbar("Не удалось создать товар в базе данных")
                    self.show_create_product_dialog(barcode)
            else:
                # Устанавливаем название по умолчанию, если товар не найден
                self.app.temp_name = f"Товар {barcode}"
                self.show_create_product_dialog(barcode)
        except Exception as e:
            print(f"Ошибка при проверке товара в облачной базе: {e}")
            self.show_snackbar(f"Ошибка при проверке товара: {str(e)}")
            # Устанавливаем название по умолчанию в случае ошибки
            self.app.temp_name = f"Товар {barcode}"
            self.show_create_product_dialog(barcode)

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
                        on_release=lambda x: dialog.dismiss()
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

        for i, existing_item in enumerate(self.app.current_invoice):
            if existing_item['product_id'] == item['product_id']:
                self.app.current_invoice[i]['quantity'] += 1  # Используем self.app.current_invoice
                self.app.current_invoice[i]['total'] = self.app.current_invoice[i]['quantity'] * \
                                                       self.app.current_invoice[i]['price']
                message = f"Добавлено: {product['name']} (x{self.app.current_invoice[i]['quantity']})"
                self.show_snackbar(message, 1.5)
                # Обновляем товары на текущем экране вместо перехода
                self.update_invoice_items()
                return

        self.app.current_invoice.append(item)
        message = f"Добавлено: {product['name']}"
        self.show_snackbar(message, 1.5)
        # Обновляем товары на текущем экране вместо перехода
        self.update_invoice_items()

    def show_create_product_dialog(self, barcode):
        """Диалог для создания нового товара"""
        self.app.temp_barcode = barcode
        # Если temp_name не установлен, устанавливаем значение по умолчанию
        if not hasattr(self.app, 'temp_name') or not self.app.temp_name:
            self.app.temp_name = f"Товар {barcode}"

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
        self.manager.current = 'product_create'

    def open_product_edit(self, product):
        """Открыть экран редактирования товара"""
        self.app.temp_product_id = product['id']
        self.manager.current = 'product_edit'

    def update_invoice_items(self):
        """Обновление списка товаров в накладной и кнопки итого"""
        if not hasattr(self, 'ids'):
            return

        # Обновляем список товаров
        if 'invoice_items' in self.ids:
            self.ids.invoice_items.clear_widgets()

            # Просто отображаем товары если они есть
            for item in self.app.current_invoice:
                icon = IconLeftWidget(icon="package-variant")
                list_item = TwoLineIconListItem(
                    text=f"{item['name']}",
                    secondary_text=f"{item['quantity']} x {item['price']:.2f} = {item['total']:.2f}",
                    on_release=lambda x, i=item: self.edit_item(i)
                )
                list_item.add_widget(icon)
                self.ids.invoice_items.add_widget(list_item)

        # Обновляем кнопку итого
        self.total_amount = sum(item['total'] for item in self.app.current_invoice)

        if 'total_button' in self.ids:
            self.ids.total_button.text = f"ИТОГО: {self.total_amount:.2f}"

            # Устанавливаем цвет в зависимости от статуса оплаты
            if self.payment_status:
                self.ids.total_button.md_bg_color = (0.2, 0.7, 0.2, 1)  # Зеленый
            else:
                self.ids.total_button.md_bg_color = (0.7, 0.2, 0.2, 1)  # Красный

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

    def save_invoice(self):
        """Сохранить накладную с учетом статуса оплаты"""
        if not self.app.current_invoice:
            self.show_snackbar("Накладная пуста! Добавьте товары.", 2.0)
            return

        # Сохраняем накладную с указанием статуса оплаты (булево значение)
        invoice_id = self.app.db.create_invoice(
            total=self.total_amount,
            payment_status=self.payment_status,  # Используем булево значение
            additional_info=""
        )

        # Сохраняем товары накладной
        for item in self.app.current_invoice:
            self.app.db.add_invoice_item(
                invoice_id=invoice_id,
                product_id=item['product_id'],
                quantity=item['quantity'],
                price=item['price'],
                total=item['total']
            )

            # Обновляем количество товара на складе
            product = self.app.db.find_product_by_id(item['product_id'])
            if product:
                new_quantity = max(0, product['quantity'] - item['quantity'])
                self.app.db.update_product_quantity(item['product_id'], new_quantity)

        # Очищаем текущую накладную
        self.app.current_invoice = []
        self.update_invoice_items()

        # Показываем уведомление
        status_text = "Оплачено" if self.payment_status else "Не оплачено"
        self.show_snackbar(f"Накладная #{invoice_id} сохранена. Статус: {status_text}", 2.0)

    def stop_scanning(self):
        """Остановка сканирования"""
        if hasattr(self, 'scanning_active') and self.scanning_active:
            self.scanning_active = False
            if self.app and hasattr(self.app, 'stop_camera'):
                self.app.stop_camera()

    def show_snackbar(self, text, duration=1.5):
        """Показать уведомление пользователю"""
        snackbar = CustomSnackbar()
        snackbar.text = text
        snackbar.duration = duration
        snackbar.pos_hint = {"center_x": 0.5, "y": 0.1}
        snackbar.size_hint_x = 0.8
        snackbar.open()


# Сохраняем класс InvoiceItemEdit из исходного кода
class InvoiceItemEdit(MDCard):
    item_quantity = NumericProperty(1)
    item_price = NumericProperty(0)

    def increment_quantity(self):
        self.item_quantity += 1

    def decrement_quantity(self):
        if self.item_quantity > 1:
            self.item_quantity -= 1