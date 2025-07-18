import pandas as pd
import psycopg2

# Caminho do seu arquivo Excel
CAMINHO_EXCEL = r'C:\Users\52414463899\Documents\Copia\empresas_filiais_formatado.xlsx' 

# Conexão com o banco PostgreSQL
def get_connection():
    return psycopg2.connect(
        dbname='pedido_de_compra',
        user='rick',
        password='mendex',
        host='localhost',
        port='5434'
    )

# Lê a coluna 'Empresa' da aba 'Sheet1'
df = pd.read_excel(CAMINHO_EXCEL, sheet_name='Sheet1', usecols=['Empresa'])

# Remove valores nulos e duplicados
df = df.dropna(subset=['Empresa']).drop_duplicates()

# Conecta ao banco
conn = get_connection()
cur = conn.cursor()

# Insere os dados
for empresa in df['Empresa']:
    cur.execute("INSERT INTO filiais (bases) VALUES (%s)", (empresa,))

# Finaliza
conn.commit()
cur.close()
conn.close()

print("Empresas inseridas com sucesso.")
