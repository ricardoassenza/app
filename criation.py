import psycopg2
from pprint import pprint
from psycopg2.errors import DuplicateColumn


def get_connection():
    return psycopg2.connect(
        dbname = 'pedido_de_compra',
        user = 'rick',
        password = 'mendex',
        host = 'localhost',
        port = '5434'
)

class Produto():
    def __init__(self, nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs, urgente, servico, status, qsms, rh, finalizado):
        self.nome = nome
        self.qtd = qtd
        self.codigo_interno = codigo_interno
        self.filial = filial
        self.solicitante = solicitante
        self.desc_orcamento = desc_orcamento
        self.obs = obs
        self.urgente = urgente
        self.servico = servico
        self.status = status
        self.qsms = qsms
        self.rh = rh
        self.finalizado = finalizado
    
    def salvar(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO pedidos_pendentes (nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs, urgente, servico, status, qsms, rh, finalizado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (self.nome, self.qtd, self.codigo_interno, self.filial, self.solicitante, self.desc_orcamento, self.obs, self.urgente, self.servico, self.status, self.qsms, self.rh, self.finalizado))
        conn.commit()
        cursor.close()
        conn.close()
        print(f'Produto "{self.nome}" salvo com sucesso!')

def create_table(tabela):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {tabela}(
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            qtd INTEGER NOT NULL,
            codigo_interno INTEGER NOT NULL,
            filial TEXT NOT NULL,              
            solicitante TEXT NOT NULL,       
            desc_orcamento TEXT NOT NULL,
            obs TEXT NOT NULL,
            urgente BOOL NOT NULL,
            servico BOOL NOT NULL,
            status TEXT,
            qsms TEXT,
            rh TEXT,
            finalizado BOOL                                                                 
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()
    
    print('tabela criada')

def delete(valor):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM produtos WHERE id = %s", (valor,))
    conn.commit()
    cur.close()
    conn.close()
    print(f"Registros onde id = {valor} foram deletados.")

def buscar(filtro, valor):
    conn = get_connection()
    cur = conn.cursor()
    
    campos_permitidos = ['nome', 'solicitante', 'id', 'codigo_interno']
    if filtro not in campos_permitidos:
        raise ValueError(f"campo '{filtro}' não permitido para exclusão")
    
    query = f"SELECT * FROM produtos WHERE {filtro} = %s"
    cur.execute(query, (valor,))
    resultado = cur.fetchall()
    cur.close()
    conn.close()
    print(resultado)
    return resultado

def adicionar_coluna(tabela,coluna):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} BOOL")
        print(f"Coluna {coluna} adicionada com sucesso.")
    except psycopg2.errors.DuplicateColumn:
        print(f"A coluna {coluna} já existe.")
        conn.rollback()
    finally:
        conn.commit()
        cur.close()
        conn.close()

def aprovados():
    conn = get_connection()
    cursor =conn.cursor()  
    # Cria a tabela se ainda não existir
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos_aprovados (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            qtd INTEGER NOT NULL,
            codigo_interno INTEGER NOT NULL,
            filial TEXT NOT NULL,              
            solicitante TEXT NOT NULL,       
            desc_orcamento TEXT NOT NULL,
            obs TEXT NOT NULL,
            urgente BOOL NOT NULL,
            servico BOOL NOT NULL,
            status TEXT,
            qsms TEXT,
            rh TEXT,
            finalizado BOOL NOT NULL                                                                    
        )
    """)

    # Limpa os dados antigos da tabela de aprovados
    cursor.execute("TRUNCATE TABLE pedidos_aprovados")

    # Copia os dados aprovados da tabela original
    cursor.execute("""
        INSERT INTO pedidos_aprovados(nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs, urgente, servico, status)
        SELECT nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs, urgente, servico, status FROM pedidos_pendentes WHERE status = 'aprovado' AND servico = FALSE 
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("Tabela 'pedidos_aprovados' atualizada com sucesso.")

def documentacao():
    conn = get_connection()
    cursor =conn.cursor()  
    # Cria a tabela se ainda não existir
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documentacao (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            qtd INTEGER NOT NULL,
            codigo_interno INTEGER NOT NULL,
            filial TEXT NOT NULL,              
            solicitante TEXT NOT NULL,       
            desc_orcamento TEXT NOT NULL,
            obs TEXT NOT NULL,
            urgente BOOL NOT NULL,
            servico BOOL NOT NULL,
            status TEXT,
            qsms TEXT,
            rh TEXT,
            finalizado BOOL NOT NULL                                                                     
        )
    """)

    # Copia os dados aprovados da tabela original
    cursor.execute("""
        INSERT INTO documentacao(nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs, urgente, servico, status, qsms, rh, finalizado)
        SELECT nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs, urgente, servico, status, qsms, rh, finalizado FROM pedidos_pendentes WHERE status = 'aprovado' AND servico = TRUE 
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("Tabela 'documentacao' atualizada com sucesso.")    

def aprovar_registros():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs, urgente, servico, status FROM pedidos_pendentes")
    rows = cursor.fetchall()

    for row in rows:
        id, nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs, urgente, servico, status = row
        print(f"ID: {id} | {nome}, {qtd}, {codigo_interno}, {filial}, {solicitante}, {desc_orcamento}, {obs}, {urgente}, {servico} | Status atual: {status}")
        resp = input("Aprovar? (s/n): ").strip().lower()

        if resp == 's':
            cursor.execute(
                "UPDATE pedidos_pendentes SET status = %s WHERE id = %s",
                ('aprovado', id)
            )
            print(f">>> ID {nome} aprovado.")
        else:
            print(f">>> ID {nome} mantido como está.")

    conn.commit()
    cursor.close()
    conn.close()
    print("Todos os registros foram processados.")
    aprovados()
    documentacao()
    deletar('pedidos_pendentes')

def documentacao_servicos():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documentacao (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            qtd INTEGER NOT NULL,
            codigo_interno INTEGER NOT NULL,
            filial TEXT NOT NULL,              
            solicitante TEXT NOT NULL,       
            desc_orcamento TEXT NOT NULL,
            obs TEXT NOT NULL,
            urgente BOOL NOT NULL,
            servico BOOL NOT NULL,
            status TEXT NOT NULL,
            qsms TEXT,
            rh TEXT,
            finalizado BOOL NOT NULL                                                                      
        )
    """)

    cursor.execute("TRUNCATE TABLE documentacao")

    cursor.execute("""
        INSERT INTO documentacao(nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs, urgente, servico, status, qsms, rh, finalizado)
        SELECT nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs, urgente, servico, status, qsms, rh, finalizado FROM produtos WHERE status = 'aprovado' AND servico = TRUE
    """)

    conn.commit()
    conn.close()
    cursor.close()
    print('tabela criada')

def historico(pasta):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        INSERT INTO historico(nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs, urgente, servico, status, qsms, rh, finalizado)
        SELECT nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs, urgente, servico, status, qsms, rh, finalizado FROM {pasta} WHERE status = 'aprovado' AND finalizado = TRUE
    """)
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Registros aprovados e finalizados da tabela '{pasta}' foram movidos para o histórico.")

def preencher_qsms_rh_interativo():
    conn = get_connection()
    cur = conn.cursor()
    
    try: 
        cur.execute("SELECT id, nome FROM documentacao")  
        rows = cur.fetchall()

        for row in rows:
            id_produto = row[0]
            nome_produto = row[1]

            print(f"\nProduto: {nome_produto} (ID: {id_produto})")
            qsms_valor = input("Digite o valor para QSMS: ")
            rh_valor = input("Digite o valor para RH: ")

            cur.execute("""
                UPDATE documentacao
                SET qsms = %s,
                    rh = %s
                WHERE id = %s
            """, (qsms_valor, rh_valor, id_produto))

        print("\nTodos os registros foram atualizados com sucesso.")
    
    except Exception as e:
        print(f"Erro ao atualizar registros: {e}")
        conn.rollback()
    
    finally:
        conn.commit()
        cur.close()
        conn.close()

def deletar(pasta):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"""TRUNCATE TABLE {pasta}""")
    conn.commit()
    cursor.close()
    conn.close()    

def finalizar_registros():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs, urgente, servico, status, finalizado FROM pedidos_aprovados")
    rows = cursor.fetchall()

    for row in rows:
        id, nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs, urgente, servico, status, finalizado = row
        print(f"ID: {id} | {nome}, {qtd}, {codigo_interno}, {filial}, {solicitante}, {desc_orcamento}, {obs}, {urgente}, {servico} , {finalizado}| Status atual: {status}")
        resp = input("finalizado? (s/n): ").strip().lower()

        if resp == 's':
            cursor.execute(
                "UPDATE pedidos_aprovados SET finalizado = %s WHERE id = %s",
                (True, id)
            )
            print(f">>> ID {nome} finalizado.")
        else:
            print(f">>> ID {nome} mantido como está.")

    conn.commit()
    cursor.close()
    conn.close()
    print("Todos os registros foram processados.")
    historico('pedidos_aprovados')
    deletar('pedidos_aprovados')
    

def inserir_documentacao():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs, urgente, servico, status, finalizado, qsms, rh FROM documentacao")
    rows = cursor.fetchall()

    for row in rows:
        id, nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs, urgente, servico, status, finalizado, qsms, rh = row
        print(f"ID: {id} | {nome}, {qtd}, {codigo_interno}, {filial}, {solicitante}, {desc_orcamento}, {obs}, {urgente}, {servico} , {finalizado}, {qsms}, {rh}| Status atual: {status}")
        respqsms = input("qsms: ").strip().lower()
        resprh = input("rh: ").strip().lower()
        cursor.execute(
            "UPDATE documentacao SET qsms = %s, rh = %s WHERE id = %s",
            (respqsms, resprh, id)
        )

    conn.commit()
    cursor.close()
    conn.close()
    print("Todos os registros foram processados.")

def aprovar_documentacao():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        INSERT INTO pedidos_aprovados(nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs, urgente, servico, status, qsms, rh, finalizado)
        SELECT nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs, urgente, servico, status, qsms, rh, finalizado FROM documentacao WHERE qsms IS NOT NULL AND rh IS NOT NULL
    """)
    conn.commit()
    cursor.close()
    conn.close()
    deletar('documentacao')
    print('documentacao movido para pedidos aprovados')