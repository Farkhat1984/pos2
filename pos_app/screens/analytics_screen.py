# screens/analytics_screen.py
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
        start_of_month = datetime(now.year, now.month, 1).strftime("%Y-%m-%d")
        self.start_date = start_of_month
        self.end_date = now.strftime("%Y-%m-%d")

        self.ids.start_date_label.text = self.start_date
        self.ids.end_date_label.text = self.end_date

        self.load_sales_analytics()

    def set_period(self, period):
        """Установка предопределенного периода"""
        now = datetime.now()

        if period == "today":
            self.start_date = now.strftime("%Y-%m-%d")
            self.end_date = now.strftime("%Y-%m-%d")
        elif period == "yesterday":
            yesterday = now - timedelta(days=1)
            self.start_date = yesterday.strftime("%Y-%m-%d")
            self.end_date = yesterday.strftime("%Y-%m-%d")
        elif period == "week":
            start_of_week = now - timedelta(days=now.weekday())
            self.start_date = start_of_week.strftime("%Y-%m-%d")
            self.end_date = now.strftime("%Y-%m-%d")
        elif period == "month":
            start_of_month = datetime(now.year, now.month, 1)
            self.start_date = start_of_month.strftime("%Y-%m-%d")
            self.end_date = now.strftime("%Y-%m-%d")
        elif period == "prev_month":
            if now.month == 1:
                start_of_prev_month = datetime(now.year - 1, 12, 1)
                end_of_prev_month = datetime(now.year, 1, 1) - timedelta(days=1)
            else:
                start_of_prev_month = datetime(now.year, now.month - 1, 1)
                end_of_prev_month = datetime(now.year, now.month, 1) - timedelta(days=1)

            self.start_date = start_of_prev_month.strftime("%Y-%m-%d")
            self.end_date = end_of_prev_month.strftime("%Y-%m-%d")

        self.ids.start_date_label.text = self.start_date
        self.ids.end_date_label.text = self.end_date
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