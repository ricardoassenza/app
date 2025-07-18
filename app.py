from flask import Flask, render_template, request, redirect, jsonify, session, url_for
import psycopg2
import smtplib
from email.message import EmailMessage
from flask import make_response
from flask import make_response, request, session, redirect

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_segura'

def get_connection():
    return psycopg2.connect(
        dbname='pedido_de_compra',
        user='rick',
        password='mendex',
        host='localhost',
        port='5434'
    )

############################ login ######################################

@app.before_request
def verificar_login():
    rotas_livres = ['login', 'static', 'liberar_pedido', 'autocomplete', 'enviar_pedido_simples', 'buscar_produtos']

    # 1. Se for rota livre, permite
    if request.endpoint in rotas_livres:
        return

    # 2. Se ninguém está logado, redireciona para login
    if not (session.get('logado') or session.get('acesso_simples') or session.get('acesso_documentador')):
        return redirect("/login")

    # 3. Se está logado como administrador
    if session.get('logado'):
        return

    # 4. Se está logado como simples
    if session.get('acesso_simples') and request.endpoint in ['pedido_novo', 'enviar_pedido_simples']:
        return

    # 5. Se está logado como documentador
    if session.get('acesso_documentador') and request.endpoint in ['documentacao', 'aprovados', 'index', 'cadastrar_produto']:
        return

    # 6. Já logado, mas tentando acessar algo sem permissão
    destino = "/"
    if session.get("acesso_simples"):
        destino = "/login"
    elif session.get("acesso_documentador"):
        destino = "/"

    html = f"""
    <script>
        alert("Seu acesso não é autorizado para esta função.");
        window.location.href = "{destino}";
    </script>
    """
    return make_response(html)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        pin = request.form['pin']
        if pin == "0205":
            session['logado'] = True
            return redirect("/pendentes")
        elif pin == "0701":
            session['acesso_documentador'] = True
            return redirect("/")  # vai para cadastro
        else:
            return redirect("/login")
    return render_template("login.html")


@app.route("/liberar_pedido", methods=["POST"])
def liberar_pedido():
    session.clear()  # limpa qualquer login anterior
    session['acesso_simples'] = True
    return redirect("/autocomplete")

############################ fazer pedido #################################

@app.route("/autocomplete")
def autocomplete():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT descricao FROM descricoes ORDER BY descricao ASC")
    descricoes = [row[0] for row in cur.fetchall()]
    cur.execute("SELECT bases FROM filiais ORDER BY bases ASC")
    filiais = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return render_template("autocomplete.html", descricoes=descricoes, filiais=filiais)

@app.route('/buscar_produtos')
def buscar_produtos():
    termo = request.args.get('q', '').strip()

    if not termo or len(termo) < 2:
        return jsonify([])

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT produto, codigo_interno 
        FROM produtos 
        WHERE produto ILIKE %s 
        LIMIT 10
    """, (f"%{termo}%",))

    resultados = cur.fetchall()
    cur.close()
    conn.close()

    # Monta resposta JSON
    sugestoes = [{"produto": linha[0], "codigo_interno": linha[1]} for linha in resultados]
    return jsonify(sugestoes)

@app.route("/enviar_pedido_simples", methods=["POST"])
def enviar_pedido_simples():
    if not session.get('acesso_simples'):
        return redirect("/login")

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

    enviar_email_novo_pedido(data)
    return render_template("pedido_enviado.html")

def enviar_email_novo_pedido(dados):
    EMAIL_ADDRESS = 'oficialloshunicos@gmail.com'
    EMAIL_PASSWORD = 'eijwmireuryaouzw'  

    msg = EmailMessage()
    msg['Subject'] = 'Novo Pedido Realizado'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = 'bherrera@serveng.com.br'

    corpo = f"""
Um novo pedido foi realizado com os seguintes dados:

Nome: {dados['nome']}
Quantidade: {dados['qtd']}
Código Interno: {dados['codigo_interno']}
Filial: {dados['filial']}
Solicitante: {dados['solicitante']}
Descrição Orçamento: {dados['desc_orcamento']}
Urgente: {"Sim" if dados.get('urgente') == 'on' else "Não"}
Serviço: {"Sim" if dados.get('servico') == 'on' else "Não"}
"""

    msg.set_content(corpo)

    try:
        print("Conectando ao servidor SMTP...")
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            print("Conectado. Logando...")
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            print("Logado. Enviando mensagem...")
            smtp.send_message(msg)
            print("Email enviado com sucesso.")
    except Exception as e:
        print("❌ Erro ao enviar e-mail:", e)

############################ pedidos pendentes ################################

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

############################ documentação de serviços ################################

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

    if qsms.strip() and rh.strip():
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM documentacao WHERE id = %s", (id_pedido,))
        dados = cursor.fetchone()

        if dados:
            cursor.execute("""
                INSERT INTO pedidos_aprovados (
                    id, nome, qtd, codigo_interno, filial, solicitante, desc_orcamento,
                    obs, urgente, servico, status, qsms, rh, finalizado
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                dados[0], dados[1], dados[2], dados[3], dados[4], dados[5], dados[6],
                dados[7], dados[8], dados[9], dados[10], qsms, rh, dados[13] if len(dados) > 13 else False
            ))

            cursor.execute("DELETE FROM documentacao WHERE id = %s", (id_pedido,))
            conn.commit()

        cursor.close()
        conn.close()

    return redirect('/documentacao')

############################ pedidos aprovados ################################

@app.route('/aprovados')
def aprovados():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs, urgente, servico, status, qsms, rh FROM pedidos_aprovados")
    pedidos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("aprovados.html", pedidos=pedidos)

############################ pedidos finalizados ################################

@app.route('/finalizar_pedido', methods=['POST'])
def finalizar_pedido():
    id_pedido = request.form['id']

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs, urgente, servico, status, qsms, rh FROM pedidos_aprovados WHERE id = %s", (id_pedido,))
    pedido = cur.fetchone()

    if pedido:
        cur.execute("""
            INSERT INTO historico (
                id, nome, qtd, codigo_interno, filial, solicitante,
                desc_orcamento, obs, urgente, servico, status, qsms, rh
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, pedido)
        cur.execute("DELETE FROM pedidos_aprovados WHERE id = %s", (id_pedido,))
        conn.commit()

    cur.close()
    conn.close()
    return redirect('/aprovados')

############################ historico ########################################

@app.route('/historico')
def historico():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nome, qtd, codigo_interno, filial, solicitante, desc_orcamento, obs, urgente, servico, status, qsms, rh FROM historico")
    pedidos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("historico.html", pedidos=pedidos)

############################ cadastrar produto ################################

@app.route("/")
def index():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, produto, codigo_interno FROM produtos")
    pedidos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("cadastro.html", pedidos=pedidos)

@app.route("/cadastrar_produto", methods=["POST"])
def cadastrar_produto():
    if not session.get('acesso_simples'):
        return redirect("/login")

    data = request.form
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO produtos (
            produto, codigo_interno
        ) VALUES (%s, %s)
    """, (
        data['produto'], data['codigo_interno']
    ))
    conn.commit()
    cur.close()
    conn.close()
    return render_template("enviado_principal.html")

if __name__ == "__main__":
    app.run(debug=True)