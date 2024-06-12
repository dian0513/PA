from sqlalchemy import create_engine, text, true
import os
from dotenv import load_dotenv
load_dotenv()  # 讀取 .env 文件中的環境變數
import pandas as pd
def init_db():
    # Replace the following values based on your database connection details

    username = os.getenv('DB_USERNAME', 'default_username')
    password = os.getenv('DB_PASSWORD', 'default_password')
    host = os.getenv('DB_HOST', 'default_host')
    database = os.getenv('DB_DATABASE', 'default_database')
    # Create database URL
    database_url = f'mysql+pymysql://{username}:{password}@{host}/{database}'

    # Create engine
    engine = create_engine(database_url)
    return engine

def select_part_v(table, **conditions):
    engine = init_db()
    if table =='0':
        table ='capacitor_info'
    else:
        table = 'mosfet_info'
    # 构建动态的WHERE子句
    where_clauses = [f"{key} = :{key}" for key in conditions.keys()]
    where_clause = " AND ".join(where_clauses)

    # 构建完整的SQL查询语句
    select_query = text(f"SELECT * FROM {table} WHERE {where_clause}")

    # 执行查询并将结果转换为JSON
    df = pd.read_sql(select_query, engine, params=conditions)
    result_json = df.to_json(orient='records', force_ascii=False)
    return result_json

