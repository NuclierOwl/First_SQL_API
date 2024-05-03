import psycopg2
from flask import Flask, jsonify, request
from psycopg2 import Error

# Конфигурация подключения к базе данных
app = Flask(__name__)
db_config = {
    'host': '192.168.1.162',
    'port': '5433',
    'database': 'user46',
    'user': 'user46',
    'password': 'y1f20'
}


# Функция для выполнения SQL-запросов
def execute_query(query):
    try:
        # Устанавливаем соединение с базой данных
        connection = psycopg2.connect(**db_config)

        # Создаем курсор для выполнения SQL-запросов
        cursor = connection.cursor()

        # Выполняем SQL-запрос
        cursor.execute(query)

        # Получаем результат выполнения запроса
        result = cursor.fetchall()

        # Закрываем курсор и соединение
        cursor.close()
        connection.close()

        # Возвращаем результат выполнения запроса
        return result

    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL:", error)


# API для работы с сенсорами
@app.route('/sensor', methods=['POST'])
def create_sensor():
    query = '''
    INSERT INTO sensors (sensor_name)
    VALUES ('new_sensor')
    RETURNING sensor_id
    '''
    sensor_id = execute_query(query)[0][0]

    measurements = request.json['sensors_measurements']

    for measurement in measurements:
        type_id = measurement['type_id']
        type_name = measurement.get('type_name')
        type_units = measurement.get('type_units')
        type_formula = measurement.get('type_formula')

        # Создаем запись о измерении в таблице sensors_measurements
        query = '''
        INSERT INTO sensors_measurements (sensor_id, type_id, type_name, type_units, type_formula)
        VALUES (%s, %s, %s, %s, %s)
        '''
        execute_query(query, (sensor_id, type_id, type_name, type_units, type_formula))

    # Получаем информацию о созданных измерениях
    query = '''
    SELECT sm.type_id, t.type_name, t.type_units, sm.type_formula
    FROM sensors_measurements sm
    JOIN measurement_types t ON t.type_id = sm.type_id
    WHERE sm.sensor_id = %s
    '''
    measurements_info = execute_query(query, (sensor_id,))

    # Формируем и возвращаем ответ
    response = {
        'sensor_id': sensor_id,
        'sensor_name': 'new_sensor',
        'sensors_measurements': measurements_info
    }
    return jsonify(response), 201


@app.route('/sensor/<int:sensor_id>', methods=['DELETE'])
def delete_sensor(sensor_id):
    # Проверяем, есть ли измерения у сенсора
    query = '''
    SELECT * FROM sensors_measurements WHERE sensor_id = %s
    '''
    measurements = execute_query(query, (sensor_id,))

    if measurements:
        return 'Невозможно удалить сенсор, так как у него есть измерения', 400

    # Удаляем записи из таблицы sensors_measurements каскадно
    query = '''
    DELETE FROM sensors_measurements WHERE sensor_id = %s
    '''
    execute_query(query, (sensor_id,))

    # Удаляет сам сенсор
    query = '''
    DELETE FROM sensors WHERE sensor_id = %s
    '''
    execute_query(query, (sensor_id,))

    return '', 204