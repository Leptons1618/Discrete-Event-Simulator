import random
from nicegui import ui
import logging

logging.basicConfig(level=logging.INFO)

def populate_table():
    data = [{'col1': str(random.randint(1, 100)), 'col2': str(random.randint(1, 100)), 'col3': str(random.randint(1, 100))} for _ in range(5)]
    table.rows = data
    logging.info(f'Table data: {data}')

columns = [
    {'name': 'col1', 'label': 'Column 1', 'field': 'col1', 'required': True, 'align': 'center'},
    {'name': 'col2', 'label': 'Column 2', 'field': 'col2', 'sortable': True, 'align': 'center'},
    {'name': 'col3', 'label': 'Column 3', 'field': 'col3', 'sortable': True, 'align': 'center'}
]

table = ui.table(columns=columns, rows=[{'col1': '', 'col2': '', 'col3': ''} for _ in range(5)], row_key='col1')
ui.button('Populate', on_click=populate_table)

ui.run(native=True, window_size=(800, 600))