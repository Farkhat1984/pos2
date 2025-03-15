# database.py
import sqlite3
import datetime
import os


class DatabaseManager:
    def __init__(self, db_path='pos_database.db'):
        """Инициализация менеджера базы данных"""
        self.db_path = db_path
        db_exists = os.path.exists(db_path)

        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = self.dict_factory
        self.cursor = self.conn.cursor()
        self.create_tables()

        if not db_exists:
            self.initialize_database()

    def dict_factory(self, cursor, row):
        """Преобразование результатов запроса в словарь"""
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def initialize_database(self):
        """Инициализация базы данных при первом создании"""
        pass

    def create_tables(self):
        """Создание необходимых таблиц в базе данных"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            cost_price REAL DEFAULT 0,
            quantity INTEGER DEFAULT 0,
            unit TEXT DEFAULT "шт",
            group_name TEXT,
            subgroup TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            total REAL NOT NULL,
            payment_status BOOL default True,
            additional_info TEXT,
            created_at TEXT,
            user_id INTEGER
        )
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            product_id INTEGER,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            total REAL NOT NULL,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
        )
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TEXT
        )
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_categories (
            product_id INTEGER,
            category_id INTEGER,
            PRIMARY KEY (product_id, category_id),
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
        )
        ''')

        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(date)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice_id ON invoice_items(invoice_id)')

        self.conn.commit()

    def find_product_by_barcode(self, barcode):
        """Поиск товара по штрих-коду"""
        self.cursor.execute("SELECT * FROM products WHERE barcode = ?", (barcode,))
        return self.cursor.fetchone()

    def find_product_by_id(self, product_id):
        """Поиск товара по ID"""
        self.cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        return self.cursor.fetchone()

    def add_product(self, barcode, name, price, cost_price=0, quantity=0, unit="шт", group="", subgroup=""):
        """Добавление нового товара"""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.cursor.execute('''
        INSERT INTO products (barcode, name, price, cost_price, quantity, unit, group_name, subgroup, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (barcode, name, price, cost_price, quantity, unit, group, subgroup, now, now))

        self.conn.commit()
        return self.cursor.lastrowid

    def update_product(self, product_id, name, price, cost_price, quantity, unit="шт", group="", subgroup=""):
        """Обновление информации о товаре"""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.cursor.execute('''
        UPDATE products
        SET name = ?, price = ?, cost_price = ?, quantity = ?, unit = ?, group_name = ?, subgroup = ?, updated_at = ?
        WHERE id = ?
        ''', (name, price, cost_price, quantity, unit, group, subgroup, now, product_id))

        self.conn.commit()
        return self.cursor.rowcount > 0

    def get_setting(self, key, default=None):
        """Получение настройки приложения"""
        self.cursor.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
        result = self.cursor.fetchone()
        return result['value'] if result else default

    def set_setting(self, key, value):
        """Установка настройки приложения"""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            self.cursor.execute(
                "UPDATE app_settings SET value = ?, updated_at = ? WHERE key = ?",
                (value, now, key)
            )

            if self.cursor.rowcount == 0:
                self.cursor.execute(
                    "INSERT INTO app_settings (key, value, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (key, value, now, now)
                )

            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка при установке настройки: {e}")
            return False

    def update_product_quantity(self, product_id, quantity):
        """Обновление только количества товара"""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.cursor.execute('''
        UPDATE products
        SET quantity = ?, updated_at = ?
        WHERE id = ?
        ''', (quantity, now, product_id))

        self.conn.commit()
        return self.cursor.rowcount > 0

    def get_all_products(self, sort_by='name'):
        """Получение всех товаров с сортировкой"""
        valid_sort_fields = ['name', 'price', 'quantity']
        sort_field = sort_by if sort_by in valid_sort_fields else 'name'

        self.cursor.execute(f"SELECT * FROM products ORDER BY {sort_field}")
        return self.cursor.fetchall()

    def search_products(self, search_term):
        """Поиск товаров по названию или штрих-коду"""
        search_param = f"%{search_term}%"

        self.cursor.execute('''
        SELECT * FROM products
        WHERE name LIKE ? OR barcode LIKE ?
        ORDER BY name
        ''', (search_param, search_param))

        return self.cursor.fetchall()

    def create_invoice(self, total, payment_status="Оплачено", additional_info=""):
        """Создание новой накладной"""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.cursor.execute('''
        INSERT INTO invoices (date, total, payment_status, additional_info, created_at)
        VALUES (?, ?, ?, ?, ?)
        ''', (now, total, payment_status, additional_info, now))

        self.conn.commit()
        return self.cursor.lastrowid

    def add_invoice_item(self, invoice_id, product_id, quantity, price, total):
        """Добавление товара в накладную"""
        self.cursor.execute('''
        INSERT INTO invoice_items (invoice_id, product_id, quantity, price, total)
        VALUES (?, ?, ?, ?, ?)
        ''', (invoice_id, product_id, quantity, price, total))

        self.conn.commit()
        return self.cursor.lastrowid

    def get_invoice(self, invoice_id):
        """Получение информации о накладной"""
        self.cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
        return self.cursor.fetchone()

    def get_invoice_items(self, invoice_id):
        """Получение товаров из накладной"""
        self.cursor.execute('''
        SELECT ii.*, p.name, p.barcode
        FROM invoice_items ii
        JOIN products p ON ii.product_id = p.id
        WHERE ii.invoice_id = ?
        ''', (invoice_id,))

        return self.cursor.fetchall()

    def get_invoices_by_period(self, start_date, end_date):
        """Получение накладных за период"""
        self.cursor.execute('''
        SELECT * FROM invoices
        WHERE date BETWEEN ? AND ?
        ORDER BY date DESC
        ''', (start_date, end_date))

        return self.cursor.fetchall()

    def get_sales_analytics(self, start_date, end_date):
        """Получение аналитики продаж за период"""
        self.cursor.execute('''
        SELECT
            SUM(i.total) as total_sales,
            COUNT(i.id) as invoice_count,
            AVG(i.total) as average_invoice,
            SUM(CASE WHEN i.payment_status = 'Оплачено' THEN i.total ELSE 0 END) as paid_amount,
            SUM(CASE WHEN i.payment_status = 'В долг' THEN i.total ELSE 0 END) as debt_amount
        FROM invoices i
        WHERE i.date BETWEEN ? AND ?
        ''', (start_date, end_date))

        return self.cursor.fetchone()

    def get_profit_analytics(self, start_date, end_date):
        """Получение аналитики прибыли за период"""
        self.cursor.execute('''
        SELECT
            SUM(ii.total) as revenue,
            SUM(ii.quantity * p.cost_price) as cost,
            SUM(ii.total) - SUM(ii.quantity * p.cost_price) as profit
        FROM invoice_items ii
        JOIN products p ON ii.product_id = p.id
        JOIN invoices i ON ii.invoice_id = i.id
        WHERE i.date BETWEEN ? AND ?
        ''', (start_date, end_date))

        return self.cursor.fetchone()

    def get_top_products(self, start_date, end_date, limit=10):
        """Получение топ-продаваемых товаров за период"""
        self.cursor.execute('''
        SELECT
            p.id, p.name, p.barcode,
            SUM(ii.quantity) as total_quantity,
            SUM(ii.total) as total_sales
        FROM invoice_items ii
        JOIN products p ON ii.product_id = p.id
        JOIN invoices i ON ii.invoice_id = i.id
        WHERE i.date BETWEEN ? AND ?
        GROUP BY p.id
        ORDER BY total_quantity DESC
        LIMIT ?
        ''', (start_date, end_date, limit))

        return self.cursor.fetchall()

    def close(self):
        """Закрытие соединения с базой данных"""
        if self.conn:
            self.conn.close()