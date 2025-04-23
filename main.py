import json
import sqlite3
from datetime import datetime, timedelta
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.storage.jsonstore import JsonStore

# Инициализация БД
conn = sqlite3.connect('gdm.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS Users
               (id INTEGER PRIMARY KEY,
                age INTEGER,
                weight REAL,
                height REAL,
                pregnancy_date TEXT)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS Measurements
               (id INTEGER PRIMARY KEY,
                date TEXT,
                bp_sys INTEGER,
                bp_dia INTEGER,
                pulse INTEGER,
                water INTEGER,
                activity BOOLEAN)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS FoodDiary
               (id INTEGER PRIMARY KEY,
                date TEXT,
                product TEXT,
                grams INTEGER,
                calories REAL)''')

# Загрузка данных о продуктах
with open('foods.json') as f:
    foods = json.load(f)

class HealthCalculator:
    @staticmethod
    def calculate_pregnancy_date(last_period):
        return (datetime.strptime(last_period, "%d.%m.%Y") - 
               timedelta(days=90) + 
               timedelta(days=7)).strftime("%d.%m.%Y")

    @staticmethod
    def calculate_bmi(weight, height):
        return round(weight / ((height/100)**2), 2)

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        
        self.add_widget(Button(text='Моё здоровье', 
                             on_press=lambda x: self.switch('health')))
        self.add_widget(Button(text='Дневники контроля',
                             on_press=lambda x: self.switch('diary')))
        self.add_widget(Button(text='Рекомендации',
                             on_press=lambda x: self.switch('recommendations')))

    def switch(self, screen):
        self.manager.current = screen

class HealthScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = GridLayout(cols=2)
        
        self.last_period = TextInput(hint_text='Дата последних месячных (дд.мм.гггг)')
        self.age = TextInput(input_filter='int', hint_text='Возраст')
        self.weight = TextInput(input_filter='float', hint_text='Вес (кг)')
        self.height = TextInput(input_filter='float', hint_text='Рост (см)')
        
        self.layout.add_widget(Label(text='Дата последних месячных:'))
        self.layout.add_widget(self.last_period)
        # ... Аналогично для остальных полей
        
        self.add_widget(self.layout)
        self.add_widget(Button(text='Сохранить', on_press=self.save_data))

    def save_data(self, instance):
        pregnancy_date = HealthCalculator.calculate_pregnancy_date(
            self.last_period.text)
        bmi = HealthCalculator.calculate_bmi(
            float(self.weight.text), 
            float(self.height.text))
        
        cursor.execute('''INSERT INTO Users 
                       (age, weight, height, pregnancy_date)
                       VALUES (?, ?, ?, ?)''',
                       (self.age.text, self.weight.text, 
                        self.height.text, pregnancy_date))
        conn.commit()

class DiaryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = GridLayout(cols=4)
        
        # Поля для ввода данных
        self.bp_sys = TextInput(hint_text='Верхнее АД')
        self.bp_dia = TextInput(hint_text='Нижнее АД')
        self.pulse = TextInput(hint_text='Пульс')
        self.water = TextInput(hint_text='Вода (мл)')
        
        # Кнопки и выбор продуктов
        self.product_spinner = Spinner(values=[f['name'] for f in foods])
        self.grams = TextInput(hint_text='Граммы')
        
        self.layout.add_widget(Label(text='Артериальное давление'))
        # ... Добавление всех элементов
        
        self.add_widget(self.layout)

    def add_food(self):
        product = next(f for f in foods if f['name'] == self.product_spinner.text)
        calories = (product['calories'] * float(self.grams.text)) / 100
        cursor.execute('''INSERT INTO FoodDiary 
                       (date, product, grams, calories)
                       VALUES (?, ?, ?, ?)''',
                       (datetime.now().strftime("%d.%m.%Y"),
                        self.product_spinner.text,
                        self.grams.text,
                        calories))
        conn.commit()

class RecommendationsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')
        
        # Расчет рекомендаций
        user = cursor.execute('SELECT * FROM Users ORDER BY id DESC LIMIT 1').fetchone()
        age = user[1]
        target_hr = 220 - age
        
        self.layout.add_widget(Label(text=f'Целевая ЧСС: {target_hr} уд/мин'))
        # ... Добавление остальных рекомендаций
        
        self.add_widget(self.layout)

class GDMMonitorApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(HealthScreen(name='health'))
        sm.add_widget(DiaryScreen(name='diary'))
        sm.add_widget(RecommendationsScreen(name='recommendations'))
        return sm

if __name__ == '__main__':
    GDMMonitorApp().run()
