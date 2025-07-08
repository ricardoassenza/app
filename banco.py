import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

connn = psycopg2.connect(
    dbname = 'postgres',
    user = 'rick',
    password = 'mendex',
    host = 'localhost',
    port = '5434'
)

connn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = connn.cursor()

cur.execute("CREATE DATABASE pedido_de_compra")
print('banco criado com sucesso')

cur.close()
connn.close()