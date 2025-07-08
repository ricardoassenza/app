from flask import Flask, render_template, request, redirect, jsonify
import psycopg2

app = Flask(__name__)

def get_connection():
    return psycopg2.connect(
        dbname='pedido_de_compra',
        user='rick',
        password='mendex',
        host='localhost',
        port='5434'
    )

@app.route("/")
def index():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs, urgente, servico, status, qsms, rh FROM pedidos_pendentes")
    pedidos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("novo_pedido.html", pedidos=pedidos)

@app.route("/novo_pedido", methods=["POST"])
def novo_pedido():
    data = request.form
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO pedidos_pendentes (
            nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs,
            urgente, servico, status, qsms, rh, finalizado
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pendente', NULL, NULL, FALSE)
    """, (
        data['nome'], data['qtd'], data['codigo_interno'], data['filial'], data['solicitante'],
        data['desc_orcamento'], data['obs'],
        data.get('urgente') == 'on', data.get('servico') == 'on'
    ))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/")

@app.route("/pendentes")
def pendentes():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs, urgente, servico FROM pedidos_pendentes")
    pedidos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("pendentes.html", pedidos=pedidos)

@app.route("/aprovar/<int:id>")
def aprovar(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT servico FROM pedidos_pendentes WHERE id = %s", (id,))
    servico = cur.fetchone()
    if servico:
        cur.execute("UPDATE pedidos_pendentes SET status = 'aprovado' WHERE id = %s", (id,))
        destino = "documentacao" if servico[0] else "pedidos_aprovados"
        cur.execute(f"""
            INSERT INTO {destino}(nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs,
                urgente, servico, status, qsms, rh, finalizado)
            SELECT nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs,
                urgente, servico, 'aprovado', NULL, NULL, FALSE
            FROM pedidos_pendentes WHERE id = %s
        """, (id,))
        cur.execute("DELETE FROM pedidos_pendentes WHERE id = %s", (id,))
        conn.commit()
    cur.close()
    conn.close()
    return redirect("/pendentes")

@app.route("/reprovar/<int:id>")
def reprovar(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM pedidos_pendentes WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/pendentes")

@app.route("/documentacao")
def documentacao():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs, urgente, servico, status, qsms, rh FROM documentacao")
    pedidos_documentacao = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("documentacao.html", documentacao=pedidos_documentacao)

@app.route('/atualizar_documentacao', methods=['POST'])
def atualizar_documentacao():
    id_pedido = request.form['id']
    qsms = request.form['qsms']
    rh = request.form['rh']

    # Garante que os dois campos estão preenchidos
    if qsms.strip() and rh.strip():
        conn = get_connection()
        cursor = conn.cursor()

        # 1. Busca a linha da tabela `documentacao`
        cursor.execute("SELECT * FROM documentacao WHERE id = %s", (id_pedido,))
        dados = cursor.fetchone()

        if dados:
            # 2. Insere na tabela `pedidos_aprovados` com os novos valores de qsms e rh
            cursor.execute("""
                INSERT INTO pedidos_aprovados (
                    id, nome, qtd, codigo_interno, filial, solicitante, desc_orcamento,
                    obs, urgente, servico, status, qsms, rh, finalizado
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                dados[0], dados[1], dados[2], dados[3], dados[4], dados[5], dados[6],
                dados[7], dados[8], dados[9], dados[10], qsms, rh, dados[13] if len(dados) > 13 else False
            ))

            # 3. Remove da tabela `documentacao`
            cursor.execute("DELETE FROM documentacao WHERE id = %s", (id_pedido,))

            conn.commit()

        cursor.close()
        conn.close()

    return redirect('/documentacao')

@app.route('/aprovados')
def aprovados():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs, urgente, servico, status, qsms, rh FROM pedidos_aprovados")
    pedidos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("aprovados.html", pedidos=pedidos)

@app.route('/finalizar_pedido', methods=['POST'])
def finalizar_pedido():
    id_pedido = request.form['id']

    conn = get_connection()
    cur = conn.cursor()

    # Buscar os dados do pedido
    cur.execute("SELECT id, nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs, urgente, servico, status, qsms, rh FROM pedidos_aprovados WHERE id = %s", (id_pedido,))
    pedido = cur.fetchone()

    if pedido:
        # Inserir no histórico (13 campos, mesmo da query acima)
        cur.execute("""
            INSERT INTO historico (
                id, nome, qtd, codigo_interno, filial, solicitante,
                desc_orcamento, obs, urgente, servico, status, qsms, rh
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, pedido)

        # Deletar da tabela de aprovados
        cur.execute("DELETE FROM pedidos_aprovados WHERE id = %s", (id_pedido,))
        conn.commit()

    cur.close()
    conn.close()
    return redirect('/aprovados')

@app.route('/historico')
def historico():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs, urgente, servico, status, qsms, rh FROM historico")
    pedidos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("historico.html", pedidos=pedidos)

if __name__ == "__main__":
    app.run(debug=True)