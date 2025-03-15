# screens/analytics_screen.py
from kivymd.uix.pickers import MDDatePicker

from pos_app.components.customsnackbar import CustomSnackbar


from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivymd.app import MDApp
from kivymd.uix.list import OneLineIconListItem, TwoLineIconListItem
from datetime import datetime, timedelta



class AnalyticsScreen(Screen):
    start_date = StringProperty("")
    end_date = StringProperty("")

    def on_enter(self):
        """Вызывается при переходе на экран"""
        now = datetime.now()
        start_of_month = datetime(now.year, now.month, 1)

        # Устанавливаем время начала и конца дня
        self.start_date = start_of_month.strftime("%Y-%m-%d 00:00:00")
        self.end_date = now.strftime("%Y-%m-%d 23:59:59")

        # Обновляем отображение дат на экране
        self.update_date_labels()

        # Загружаем аналитику
        self.load_sales_analytics()

    def update_date_labels(self):
        """Обновление отображения дат на экране"""
        if hasattr(self, 'ids') and 'start_date_label' in self.ids and 'end_date_label' in self.ids:
            # Форматируем даты для отображения
            start = datetime.strptime(self.start_date, "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y")
            end = datetime.strptime(self.end_date, "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y")

            self.ids.start_date_label.text = start
            self.ids.end_date_label.text = end

    def show_date_picker(self, date_type):
        """Отображение диалога выбора даты"""
        try:
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
        except ValueError as e:
            app = MDApp.get_running_app()
            CustomSnackbar(
                text=f"Ошибка формата даты: {str(e)}",
                snackbar_x="10dp",
                snackbar_y="10dp",
            ).open()

    def on_date_select(self, date, date_type):
        """Обработка выбора даты"""
        selected_date = date.strftime("%Y-%m-%d")
        if date_type == 'start':
            self.start_date = f"{selected_date} 00:00:00"
        else:
            self.end_date = f"{selected_date} 23:59:59"

        self.update_date_labels()
        self.load_sales_analytics()
    def load_sales_analytics(self):
        """Загрузка данных о продажах за период"""
        app = MDApp.get_running_app()
        sales_data = app.db.get_sales_analytics(self.start_date, self.end_date)
        self.ids.analytics_results.clear_widgets()

        if not sales_data or not sales_data['total_sales']:
            self.ids.analytics_results.add_widget(
                OneLineIconListItem(text="Нет данных о продажах за выбранный период")
            )
            return

        self.ids.analytics_results.add_widget(
            OneLineIconListItem(text=f"Общая сумма продаж: {sales_data['total_sales']:.2f}")
        )
        self.ids.analytics_results.add_widget(
            OneLineIconListItem(text=f"Количество накладных: {sales_data['invoice_count']}")
        )
        self.ids.analytics_results.add_widget(
            OneLineIconListItem(text=f"Средний чек: {sales_data['average_invoice']:.2f}")
        )
        self.ids.analytics_results.add_widget(
            OneLineIconListItem(text=f"Оплачено: {sales_data['paid_amount']:.2f}")
        )
        self.ids.analytics_results.add_widget(
            OneLineIconListItem(text=f"В долг: {sales_data['debt_amount']:.2f}")
        )

        profit_data = app.db.get_profit_analytics(self.start_date, self.end_date)

        if profit_data and profit_data['revenue']:
            self.ids.analytics_results.add_widget(
                OneLineIconListItem(text=f"Выручка: {profit_data['revenue']:.2f}")
            )
            self.ids.analytics_results.add_widget(
                OneLineIconListItem(text=f"Себестоимость: {profit_data['cost']:.2f}")
            )
            self.ids.analytics_results.add_widget(
                OneLineIconListItem(text=f"Прибыль: {profit_data['profit']:.2f}")
            )

        top_products = app.db.get_top_products(self.start_date, self.end_date, 5)

        if top_products:
            self.ids.analytics_results.add_widget(
                OneLineIconListItem(text="Топ-5 продаваемых товаров:")
            )

            for i, product in enumerate(top_products, 1):
                self.ids.analytics_results.add_widget(
                    TwoLineIconListItem(
                        text=f"{i}. {product['name']}",
                        secondary_text=f"Продано: {product['total_quantity']} на сумму: {product['total_sales']:.2f}"
                    )
                )

    def load_profit_analytics(self):
        """Загрузка данных о прибыли за период"""
        app = MDApp.get_running_app()
        profit_data = app.db.get_profit_analytics(self.start_date, self.end_date)
        self.ids.analytics_results.clear_widgets()

        if not profit_data or not profit_data['revenue']:
            self.ids.analytics_results.add_widget(
                OneLineIconListItem(text="Нет данных о прибыли за выбранный период")
            )
            return

        self.ids.analytics_results.add_widget(
            OneLineIconListItem(text=f"Выручка: {profit_data['revenue']:.2f}")
        )
        self.ids.analytics_results.add_widget(
            OneLineIconListItem(text=f"Себестоимость: {profit_data['cost']:.2f}")
        )
        self.ids.analytics_results.add_widget(
            OneLineIconListItem(text=f"Прибыль: {profit_data['profit']:.2f}")
        )

        if profit_data['revenue'] > 0:
            margin = (profit_data['profit'] / profit_data['revenue']) * 100
            self.ids.analytics_results.add_widget(
                OneLineIconListItem(text=f"Рентабельность: {margin:.2f}%")
            )