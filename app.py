
from flask import Flask, render_template, request, redirect, url_for, send_file, session, Response
import psycopg2
import csv
import json
import io
import os
import re
from datetime import datetime, timedelta, timezone, timedelta   
import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment, Font
import tempfile
from datetime import datetime
import hashlib
from flask import render_template, request, redirect, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'  # Importante para sessões

VERSAO_ATUAL = "v1.3"

CONFIG_FILE = 'config.json'

def carregar_config():
    config_padrao = {
        "formulario_ativo": True,
        "audicao_ativa": True
    }

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            try:
                config_arquivo = json.load(file)
                # Atualizar config_padrao com o que tiver no arquivo
                config_padrao.update(config_arquivo)
            except json.JSONDecodeError:
                # Arquivo corrompido, volta para padrão
                pass

    return config_padrao

def salvar_config(config):
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file, indent=4)


@app.context_processor
def inject_version():
    return dict(versao=VERSAO_ATUAL)

def criptografar_senha(senha):
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()


def admin_required(func):
    from functools import wraps
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if 'usuario' not in session or session.get('nivel') != 'Admin':
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return decorated_view

def calcular_idade(data_nascimento):
    if data_nascimento:
        nascimento = datetime.strptime(data_nascimento, '%Y-%m-%d')
        hoje = datetime.today()
        idade = hoje.year - nascimento.year - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))
        return idade
    return None

@app.route('/menu')
def menu():
    if 'usuario' not in session:
        return redirect('/login')
    return render_template('menu.html')

@app.route('/verificar_cadastro', methods=['POST'])
def verificar_cadastro():
    data = request.get_json()
    nome = data.get('nome').strip().upper()
    nascimento = data.get('nascimento').strip()

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inscritos WHERE UPPER(nome) = %s AND nascimento = %s", (nome, nascimento))
    resultado = cursor.fetchone()

    if resultado:
        keys = [desc[0] for desc in cursor.description]
        dados = dict(zip(keys, resultado))
        conn.close()
        return jsonify({"existe": True, "dados": dados})
    else:
        conn.close()
        return jsonify({"existe": False})


    
@app.route('/cadastro_existente')
def cadastro_existente():
    nome = request.args.get('nome', 'Usuário')  # Se não vier nome, mostra 'Usuário'
    return render_template('cadastro_existente.html', nome=nome)



def conectar():
    print("🎯 CONECTANDO NO BANCO -> banco_gc0v no HOST: dpg-d0ogdqemcj7s73d5icug-a.oregon-postgres.render.com")
    return psycopg2.connect(
        dbname="banco_gc0v",
        user="banco_gc0v_user",
        password="0yP4ybAuaGiG7XC5Fsq1cn3Tzjjx6s0m",
        host="dpg-d0ogdqemcj7s73d5icug-a.oregon-postgres.render.com",
        port="5432"
    )


# ===============================
# Login e Controle de Sessão
# ===============================

@app.route('/login', methods=['GET', 'POST'])
def login():
    print("🚀 LOGIN acionado")
    erro = None
    if request.method == 'POST':
        usuario = request.form['usuario'].strip().lower()
        senha = request.form['senha'].strip()

        print(f"🧠 Usuario digitado: {usuario}")
        print(f"🧠 Senha digitada (criptografada): {criptografar_senha(senha)}")

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT senha, nivel FROM usuarios WHERE usuario = %s", (usuario,))
        resultado = cursor.fetchone()
        conn.close()

        if resultado:
            senha_correta, nivel = resultado

            print(f"🔑 Senha no banco: {senha_correta}")

            if criptografar_senha(senha) == senha_correta.strip():
                session['usuario'] = usuario
                session['nivel'] = nivel
                return redirect('/menu')
            else:
                erro = "Senha incorreta!"
        else:
            erro = "Usuário não encontrado!"

    return render_template('login.html', erro=erro)



@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ===============================
# Cadastro e Visualizações
# ===============================

@app.route('/', methods=['GET', 'POST'])
def form():
    config = carregar_config()
    if not config.get('formulario_ativo', True):
        return render_template('form.html', mostrar_modal=True)
    sucesso = False
    erro = False
    if request.method == 'POST':
        try:
            dados = request.form.to_dict(flat=True)
            dados['nome'] = dados.get('nome', '').upper()
            dados['email'] = dados.get('email', '').lower()

            campos_title = ['endereco', 'bairro', 'cidade', 'estado', 'profissao']
            for campo in campos_title:
                if campo in dados and dados[campo]:
                    dados[campo] = dados[campo].title()

            conn = conectar()
            cursor = conn.cursor()

            if dados.get('id'):  # Se existe ID, faz UPDATE (alteração)
                cursor.execute('''
                    UPDATE inscritos SET
                        nome=%s, nascimento=%s, telefone=%s, email=%s, endereco=%s, numero=%s, complemento=%s,
                        bairro=%s, cidade=%s, estado=%s, profissao=%s, estado_civil=%s, batizado=%s, perfil=%s,
                        voz=%s, aulas=%s, segunda_voz=%s, instrumentos=%s, outro_instrumento=%s, cifras=%s, ouvido=%s,
                        nivel_tecnico=%s, ensaios=%s, cultos=%s, motivacao=%s, experiencia=%s
                    WHERE id=%s
                ''', (
                    dados.get('nome'), dados.get('nascimento'), dados.get('telefone'), dados.get('email'),
                    dados.get('endereco'), dados.get('numero'), dados.get('complemento'), dados.get('bairro'),
                    dados.get('cidade'), dados.get('estado'), dados.get('profissao'), dados.get('estado_civil'),
                    dados.get('batizado'), dados.get('perfil'), dados.get('voz'), dados.get('aulas'),
                    dados.get('segunda_voz'), dados.get('instrumentos'), dados.get('outro_instrumento'),
                    dados.get('cifras'), dados.get('ouvido'), dados.get('nivel_tecnico'),
                    dados.get('ensaios'), dados.get('cultos'), dados.get('motivacao'), dados.get('experiencia'),
                    dados.get('id')  # ID vai na cláusula WHERE
                ))
            else:  # Se não existe ID, faz INSERT (novo cadastro)
                cursor.execute('''
                    INSERT INTO inscritos (
                        nome, nascimento, telefone, email, endereco, numero, complemento,
                        bairro, cidade, estado, profissao, estado_civil, batizado, perfil,
                        voz, aulas, segunda_voz, instrumentos, outro_instrumento, cifras, ouvido,
                        nivel_tecnico, ensaios, cultos, motivacao, experiencia
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    dados.get('nome'), dados.get('nascimento'), dados.get('telefone'), dados.get('email'),
                    dados.get('endereco'), dados.get('numero'), dados.get('complemento'), dados.get('bairro'),
                    dados.get('cidade'), dados.get('estado'), dados.get('profissao'), dados.get('estado_civil'),
                    dados.get('batizado'), dados.get('perfil'), dados.get('voz'), dados.get('aulas'),
                    dados.get('segunda_voz'), dados.get('instrumentos'), dados.get('outro_instrumento'),
                    dados.get('cifras'), dados.get('ouvido'), dados.get('nivel_tecnico'),
                    dados.get('ensaios'), dados.get('cultos'), dados.get('motivacao'), dados.get('experiencia')
                ))

            conn.commit()
            conn.close()
            return redirect('/sucesso')
        except Exception as e:
            print(e)
            erro = True


    return render_template('form.html', sucesso=sucesso, erro=erro)

@app.route('/sucesso')
def sucesso():
    return render_template('sucesso.html')

@app.route('/inscritos')
def inscritos():
    if 'usuario' not in session:
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM inscritos ORDER BY nome ASC')
    inscritos = cursor.fetchall()
    conn.close()

    inscritos_formatados = []
    for inscrito in inscritos:
        inscrito = list(inscrito)

        # Calcular idade de forma segura
        try:
            if inscrito[2] is not None:
                idade = calcular_idade(str(inscrito[2]))
            else:
                idade = None
        except Exception:
            idade = None
        inscrito.append(idade)

        # Formatar data de nascimento de forma segura
        try:
            if inscrito[2] is not None:
                data = datetime.strptime(str(inscrito[2]), "%Y-%m-%d")
                inscrito[2] = data.strftime("%d/%m/%Y")
            else:
                inscrito[2] = "Data não informada"
        except Exception:
            inscrito[2] = "Data inválida"

        inscritos_formatados.append(inscrito)

    return render_template('inscritos.html', inscritos=inscritos_formatados)



@app.route('/gerenciar')
def gerenciar():
    if 'usuario' not in session:
        return redirect('/login')
    if session['nivel'] != 'admin':
        return redirect('/acesso_negado')

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM inscritos ORDER BY nome ASC')
    inscritos = cursor.fetchall()
    conn.close()
    return render_template('gerenciar.html', inscritos=inscritos)

@app.route('/acesso_negado')
def acesso_negado():
    if 'usuario' not in session:
        return redirect('/login')
    return render_template('acesso_negado.html')

@app.route('/inativar/<int:id>')
def inativar(id):
    if 'usuario' not in session or session['nivel'] != 'admin':
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('UPDATE inscritos SET ativo = 0 WHERE id = %s', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('gerenciar'))

@app.route('/ativar/<int:id>')
def ativar(id):
    if 'usuario' not in session or session['nivel'] != 'admin':
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('UPDATE inscritos SET ativo = 1 WHERE id = %s', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('gerenciar'))

@app.route('/excluir/<int:id>')
def excluir(id):
    if 'usuario' not in session or session['nivel'] != 'admin':
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM inscritos WHERE id = %s', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('gerenciar'))

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    if 'usuario' not in session or session['nivel'] != 'admin':
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()

    if request.method == 'POST':
        dados = request.form.to_dict(flat=True)
        dados['nome'] = dados.get('nome', '').upper()
        dados['email'] = dados.get('email', '').lower()

        campos_title = ['endereco', 'bairro', 'cidade', 'estado', 'profissao']
        for campo in campos_title:
            if campo in dados and dados[campo]:
                dados[campo] = dados[campo].title()

        cursor.execute('''
            UPDATE inscritos SET
                nome=%s, nascimento=%s, telefone=%s, email=%s, endereco=%s, numero=%s, complemento=%s,
                bairro=%s, cidade=%s, estado=%s, profissao=%s, estado_civil=%s, batizado=%s, perfil=%s,
                voz=%s, aulas=%s, segunda_voz=%s, instrumentos=%s, outro_instrumento=%s, cifras=%s, ouvido=%s,
                nivel_tecnico=%s, ensaios=%s, cultos=%s, motivacao=%s, experiencia=%s
            WHERE id=%s
        ''', (
            dados.get('nome'), dados.get('nascimento'), dados.get('telefone'), dados.get('email'),
            dados.get('endereco'), dados.get('numero'), dados.get('complemento'), dados.get('bairro'),
            dados.get('cidade'), dados.get('estado'), dados.get('profissao'), dados.get('estado_civil'),
            dados.get('batizado'), dados.get('perfil'), dados.get('voz'), dados.get('aulas'),
            dados.get('segunda_voz'), dados.get('instrumentos'), dados.get('outro_instrumento'),
            dados.get('cifras'), dados.get('ouvido'), dados.get('nivel_tecnico'),
            dados.get('ensaios'), dados.get('cultos'), dados.get('motivacao'), dados.get('experiencia'), id
        ))
        conn.commit()
        conn.close()
        return redirect(url_for('gerenciar'))

    cursor.execute('SELECT * FROM inscritos WHERE id = %s', (id,))
    inscrito = cursor.fetchone()
    conn.close()
    return render_template('editar.html', inscrito=inscrito)

@app.route('/detalhes/<int:id>')
def detalhes(id):
    if 'usuario' not in session:
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM inscritos WHERE id = %s', (id,))
    inscrito = cursor.fetchone()
    conn.close()
    return render_template('detalhes.html', inscrito=inscrito)

@app.route('/exportar')
def exportar():
    if 'usuario' not in session:
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM inscritos ORDER BY nome ASC')
    inscritos = cursor.fetchall()
    conn.close()

    with open('inscritos.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Nome', 'Nascimento', 'Telefone', 'Email', 'Endereço', 'Número', 'Complemento',
                         'Bairro', 'Cidade', 'Estado', 'Profissão', 'Estado Civil', 'Batizado', 'Perfil',
                         'Classificação Vocal', 'Aulas', 'Segunda Voz', 'Instrumentos', 'Outro Instrumento',
                         'Sabe Cifras', 'Ouvido', 'Nível Técnico', 'Ensaios', 'Cultos', 'Motivação', 'Experiência', 'Status'])
        for i in inscritos:
            writer.writerow(i[1:-1])

    return send_file('inscritos.csv', as_attachment=True)

@app.route('/exportar_csv')
def exportar_xlsx():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM inscritos ORDER BY nome ASC')
    inscritos = cursor.fetchall()
    conn.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Inscritos"

    # Títulos
    ws.merge_cells('A1:Z1')
    ws['A1'] = 'PENIEL GUILHERMINA'
    ws['A1'].alignment = Alignment(horizontal='center')
    ws['A1'].font = Font(size=16, bold=True)

    ws.merge_cells('A2:Z2')
    ws['A2'] = 'Cadastro Ministério de Louvor'
    ws['A2'].alignment = Alignment(horizontal='center')
    ws['A2'].font = Font(size=12, bold=True)

    # Cabeçalhos
    cabecalhos = ['Nome', 'Nascimento', 'Telefone', 'Email', 'Endereço', 'Número', 'Complemento',
                  'Bairro', 'Cidade', 'Estado', 'Profissão', 'Estado Civil', 'Batizado', 'Perfil',
                  'Voz', 'Aulas', 'Segunda Voz', 'Instrumentos', 'Cifras', 'Ouvido',
                  'Nível Técnico', 'Ensaios', 'Cultos', 'Motivação', 'Experiência', 'Status']

    for col_num, header in enumerate(cabecalhos, 1):
        cell = ws.cell(row=3, column=col_num)
        cell.value = header
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')

    # Dados
    for row_num, inscrito in enumerate(inscritos, start=4):
        dados = [
            inscrito[1], inscrito[2], inscrito[3], inscrito[4], inscrito[5], inscrito[6],
            inscrito[7], inscrito[8], inscrito[9], inscrito[10], inscrito[11], inscrito[12],
            inscrito[13], inscrito[14], inscrito[15], inscrito[16], inscrito[17], inscrito[18],
            inscrito[19], inscrito[20], inscrito[21], inscrito[22], inscrito[23], inscrito[24],
            inscrito[25], 'Ativo' if inscrito[27] == 1 else 'Inativo'
        ]
        for col_num, dado in enumerate(dados, 1):
            ws.cell(row=row_num, column=col_num).value = dado

    # Ajuste automático das larguras
    for col in ws.columns:
        max_length = 0
        column = get_column_letter(col[0].column)
        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        adjusted_width = max_length + 2
        ws.column_dimensions[column].width = adjusted_width

    # Salvar e retornar
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    wb.save(temp_file.name)
    temp_file.seek(0)
    return send_file(temp_file.name, as_attachment=True, download_name='inscritos.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@app.route('/senhas')
def senhas():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios")
    usuarios = cursor.fetchall()
    conn.close()
    return render_template('senhas.html', usuarios=usuarios)

@app.route('/novo_usuario', methods=['GET', 'POST'])
def novo_usuario():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = criptografar_senha(request.form['senha'])
        nivel = request.form['nivel']

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (usuario, senha, nivel) VALUES (%s, %s, %s)", (usuario, senha, nivel))
        conn.commit()
        conn.close()
        return redirect(url_for('senhas'))
    return render_template('novo_usuario.html')


@app.route('/excluir_usuario/<int:id>')
def excluir_usuario(id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = %s", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('senhas'))

@app.route('/adicionar_campo', methods=['POST'])
def adicionar_campo():
    if request.method == 'POST':
        nome_campo = request.form.get('nova_pergunta')
        tipo_resposta = request.form.get('tipo_resposta')

        if nome_campo:
            adicionar_coluna_se_necessario(nome_campo.replace(' ', '_').lower())

        return redirect('/layout')

@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    conn = conectar()
    cursor = conn.cursor()

    try:
        if request.method == 'POST':
            usuario = request.form.get('usuario').strip()
            senha = request.form.get('senha', '').strip()
            nivel = request.form.get('nivel').strip().lower()

            if senha:
                senha = criptografar_senha(senha)
                cursor.execute("UPDATE usuarios SET usuario = %s, senha = %s, nivel = %s WHERE id = %s", (usuario, senha, nivel, id))
            else:
                cursor.execute("UPDATE usuarios SET usuario = %s, nivel = %s WHERE id = %s", (usuario, nivel, id))

            conn.commit()
            return redirect(url_for('senhas'))

        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id,))
        usuario = cursor.fetchone()
        if not usuario:
            flash('Usuário não encontrado!', 'error')
            return redirect(url_for('senhas'))
        return render_template('editar_usuario.html', usuario=usuario)

    except Exception as e:
        conn.rollback()
        flash(f'Erro ao atualizar usuário: {e}', 'error')
        return redirect(url_for('senhas'))

    finally:
        conn.close()


@app.route('/form')
def redirecionar_para_form():
    return redirect('/')


@app.route('/configuracoes', methods=['GET', 'POST'])
def configuracoes_page():
    if 'usuario' not in session:
        return redirect('/login')

    config = carregar_config()

    if request.method == 'POST':
        config['formulario_ativo'] = 'formulario_ativo' in request.form
        config['audicao_ativa'] = 'audicao_ativa' in request.form
        salvar_config(config)  

    return render_template(
        'configuracoes.html',
        formulario_ativo=config['formulario_ativo'],
        audicao_ativa=config['audicao_ativa']
    )

@app.route('/audicoes', methods=['GET', 'POST'])
def audicoes():
    config = carregar_config()
    if not config.get('audicao_ativa', True):
        return render_template('audicoes.html', mostrar_modal=True)

    if request.method == 'POST':
        nome = request.form['nome'].strip().upper()
        telefone = request.form['telefone'].strip()
        musica = request.form['musica'].strip().title()
        link_youtube = request.form['link_youtube'].strip()
        tom = request.form['tom']
        if tom == 'Outro':
            tom = request.form.get('outro_tom').strip().upper()

        tipo = request.form['instrumento_voz']
        detalhe = ''

        if tipo == 'INSTRUMENTO' or tipo == 'AMBOS':
            instrumento = request.form.get('instrumento_escolhido')
            if instrumento == 'Outro':
                detalhe = request.form.get('outro_instrumento').strip().title()
            else:
                detalhe = instrumento
        else:
            detalhe = None

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO audicoes (nome, telefone, musica, link_youtube, tom, instrumento_voz, detalhe_instrumento, data_envio)
            VALUES (%s, %s, %s, %s, %s, %s, %s, now())
        ''', (nome, telefone, musica, link_youtube, tom, tipo, detalhe))

        conn.commit()
        cursor.close()
        conn.close()

        return render_template('sucesso.html')

    return render_template('audicoes.html')



@app.route('/audicoes_gerencia')
def audicoes_gerencia():
    if 'usuario' not in session:
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM audicoes
        WHERE arquivado = FALSE
        ORDER BY data_envio DESC
    ''')
    dados = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('audicoes_gerencia.html', dados=dados)



@app.template_filter('youtube_id')
def youtube_id(link):
    regex = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(regex, link)
    return match.group(1) if match else ''

@app.template_filter('strftime_brasil')
def _jinja2_filter_datetime_brasil(value, fmt=None):
    if not value:
        return ""
    try:
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return value
        value = value - timedelta(hours=3)
        return value.strftime(fmt or "%d/%m/%y - %H:%M:%S")
    except Exception:
        return str(value)
    
@app.route('/excluir_audicao/<int:id>')
def excluir_audicao(id):
    if 'usuario' not in session:
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM audicoes WHERE id = %s', (id,))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('audicoes_gerencia'))

@app.route('/arquivar_audicao/<int:id>')
def arquivar_audicao(id):
    if 'usuario' not in session:
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE audicoes SET arquivado = TRUE WHERE id = %s
    ''', (id,))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('audicoes_gerencia'))

@app.route('/audicoes_arquivadas')
def audicoes_arquivadas():
    if 'usuario' not in session:
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM audicoes
        WHERE arquivado = TRUE
        ORDER BY data_envio DESC
    ''')
    dados = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('audicoes_arquivadas.html', dados=dados)

@app.route('/desarquivar_audicao/<int:id>')
def desarquivar_audicao(id):
    if 'usuario' not in session:
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE audicoes SET arquivado = FALSE WHERE id = %s
    ''', (id,))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('audicoes_arquivadas'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    #app.run(debug=True)
