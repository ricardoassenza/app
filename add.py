import psycopg2 
from criation import adicionar_coluna, remover_coluna
import pandas as pd

def get_connection():
    return psycopg2.connect(
        dbname = 'pedido_de_compra',
        user = 'rick',
        password = 'mendex',
        host = 'localhost',
        port = '5434'
)

caminho = r'C:\Users\52414463899\Documents\Copia\filiais.xlsx'  

df = pd.read_excel(caminho, sheet_name='Planilha1', usecols=['bases'])

# Remove valores nulos e duplicados
df = df.dropna(subset=['bases']).drop_duplicates()

# Conecta ao banco
conn = get_connection()
cur = conn.cursor()

# Insere os dados
for base in df['bases']:
    cur.execute("INSERT INTO filiais (bases) VALUES (%s)", (base,))

# Finaliza
conn.commit()
cur.close()
conn.close()

print("Empresas inseridas com sucesso.")
