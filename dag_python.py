from airflow import DAG
from datetime import datetime, timedelta, date
from airflow.operators.dummy_operator import DummyOperator
from airflow.providers.potgres.operators.postgres import PostgresOperator
from airflow.utils.task_group import TaskGroup
from airflow.models import Variable

LOAD_PART_TABLE = "select std0.f_load_simple_partition('std0.lineitem','l_shipdate', '1997-02-01', '1997-03-01', 'dl.lineitem','admin', 'vtVVscma3zqqrrww')"

DB_CONN = "gp_sapiens_std0"
DB_SCHEMA = 'std0'
DB_PROC_LOAD = 'f_load_full'
FULL_LOAD_TABLES = ['region']
FULL_LOAD_FILES = {'region':'region'}
MD_TABLE_LOAD_QUERY = f"select {DB_SCHEMA}.{DB_PROC_LOAD}(%(tab_name)s, %(file_name)s);"
default_args = {
    'depends_on_past': False,
    'owner': 'std0',
    'start_date': datetime(2020, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
    "task_dag",
    max_active_runs=3,
    schedule_interval=None,
    default_args=default_args,
    catchup=False,
) as dag:

    task_start = DummyOperator(task_id='start')
    task_part = PostgresOperator(task_id="start_insert_fact",
                                 postgres_conn_id="gp_sapiens_std0",
                                 sql=LOAD_PART_TABLE
                                 )
    with TaskGroup("full_insert") as task_full_insert_tables:
        for table in FULL_LOAD_TABLES:
            task = PostgresOperator(task_id=f"load_table_{table}",
                                    postgres_conn_id=DB_CONN,
                                    sql=MD_TABLE_LOAD_QUERY,
                                    parameters={'tab_name': f'{DB_SCHEMA}.{table}', 'file_name': f'{FULL_LOAD_FILES["region"]}'}
                                    )

    task_end = DummyOperator(task_id='end')

    task_start >> task_part >> task_full_insert_tables >> task_end






from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.dummy_operator import DummyOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.utils.task_group import TaskGroup

# Конфигурационные константы
DB_CONN = "gp_sapiens_std15_122"  # ID подключения в Airflow Connections
DB_SCHEMA = 'std15_122'  # Схема базы данных
DB_USER = 'intern'  # Пользователь для подключения
DB_PASS = 'intern'  # Пароль для подключения

# УНИВЕРСАЛЬНЫЙ SQL ШАБЛОН ДЛЯ ВСЕХ ФУНКЦИЙ
SQL_TEMPLATE = "SELECT {schema}.{function_name}({parameters});"

# 1. КОНФИГУРАЦИЯ ВЫЗОВОВ ФУНКЦИЙ
FUNCTION_CALLS = {
    # Функции загрузки таблиц измерений (справочники)
    'dimensions': [
        {
            'task_id': 'load_region',
            'function': 'f_load_full',
            'params': ['region', 'region']  # table_name, file_name
        },
        {
            'task_id': 'load_price',
            'function': 'f_load_full',
            'params': ['price', 'price']
        },
        {
            'task_id': 'load_product',
            'function': 'f_load_full',
            'params': ['product', 'product']
        },
        {
            'task_id': 'load_chanel',
            'function': 'f_load_full',
            'params': ['chanel', 'chanel']
        }
    ],

    # Функции загрузки таблиц фактов
    'facts': [
        {
            'task_id': 'load_sales',
            'function': 'f_load_simple_partition',
            'params': [
                f'{DB_SCHEMA}.sales',  # target_table
                'date',  # partition_key
                '2021-03-01',  # start_date
                '2021-04-01',  # end_date
                'gp.sales',  # source_table
                DB_USER,  # user_id
                DB_PASS  # password
            ]
        },
        {
            'task_id': 'load_plan',
            'function': 'f_load_simple_partition',
            'params': [
                f'{DB_SCHEMA}.plan',  # target_table
                'date',  # partition_key
                '2021-03-01',  # start_date
                '2021-04-01',  # end_date
                'gp.plan',  # source_table
                DB_USER,  # user_id
                DB_PASS  # password
            ]
        }
    ],

    # Функция создания витрины
    'data_mart': [
        {
            'task_id': 'create_plan_fact_sales_mart',
            'function': 'plan_fact_sales',
            'params': ['2021-03-01']  # month_date
        }
    ],

    # Функция создания представления
    'views': [
        {
            'task_id': 'create_plan_fact_view',
            'function': 'create_plan_fact_view',
            'params': ['2021-03-01']  # month_date
        }
    ]
}


def generate_sql_call(function_name, params):
    """Генерирует SQL вызов функции с параметрами"""
    # Форматируем параметры в виде строки для SQL
    params_str = ', '.join([f"'{p}'" if isinstance(p, str) else str(p) for p in params])
    return SQL_TEMPLATE.format(
        schema=DB_SCHEMA,
        function_name=function_name,
        parameters=params_str
    )


# Параметры DAG
default_args = {
    'depends_on_past': False,
    'owner': 'std15_122',
    'start_date': datetime(2024, 1, 14),
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

# СОЗДАНИЕ DAG
with DAG(
        "std15_122_plan_fact_sales_reporting_etl",
        description="ETL пайплайн с унифицированным вызовом функций",
        max_active_runs=3,
        schedule_interval='15 0 * * *',  # каждый день в 00:15
        default_args=default_args,
        catchup=False,
        tags=['std15_122']
) as dag:
    # 1. СТАРТ ПАЙПЛАЙНА
    start = DummyOperator(task_id='start_etl_process')

    # 2. ЗАГРУЗКА ТАБЛИЦ ИЗМЕРЕНИЙ
    with TaskGroup("load_dimensions") as dimensions_group:
        for func_config in FUNCTION_CALLS['dimensions']:
            sql = generate_sql_call(func_config['function'], func_config['params'])
            PostgresOperator(
                task_id=func_config['task_id'],
                postgres_conn_id=DB_CONN,
                sql=sql
            )

    # 3. ЗАГРУЗКА ТАБЛИЦ ФАКТОВ
    with TaskGroup("load_facts") as facts_group:
        for func_config in FUNCTION_CALLS['facts']:
            sql = generate_sql_call(func_config['function'], func_config['params'])
            PostgresOperator(
                task_id=func_config['task_id'],
                postgres_conn_id=DB_CONN,
                sql=sql
            )

    # 4. СОЗДАНИЕ ВИТРИНЫ
    with TaskGroup("create_data_marts") as marts_group:
        for func_config in FUNCTION_CALLS['data_mart']:
            sql = generate_sql_call(func_config['function'], func_config['params'])
            PostgresOperator(
                task_id=func_config['task_id'],
                postgres_conn_id=DB_CONN,
                sql=sql
            )

    # 5. СОЗДАНИЕ ПРЕДСТАВЛЕНИЙ (ПРЕДПОСЛЕДНИЙ ШАГ)
    with TaskGroup("create_views") as views_group:
        for func_config in FUNCTION_CALLS['views']:
            sql = generate_sql_call(func_config['function'], func_config['params'])
            PostgresOperator(
                task_id=func_config['task_id'],
                postgres_conn_id=DB_CONN,
                sql=sql
            )

    # 6. ЗАВЕРШЕНИЕ ПАЙПЛАЙНА (ПОСЛЕДНИЙ ШАГ)
    end = DummyOperator(task_id='end_etl_process')

    # ЗАВИСИМОСТИ: предпоследний шаг - создание представления
    start >> dimensions_group >> facts_group >> marts_group >> views_group >> end