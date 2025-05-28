
# 📄 Documentação Técnica - Formulário de Louvor Peniel

## 📌 Visão Geral
Este projeto é um sistema de cadastro online para músicos que desejam participar do Ministério de Louvor da Igreja Peniel. Desenvolvido em **Python com Flask**, permite gerenciar cadastros, audições, usuários e configurações de forma simples e eficiente.

---

## 🚀 Tecnologias Utilizadas
- 🐍 Python 3.x
- 🔥 Flask
- 🗄️ SQLite ou PostgreSQL
- 🌐 HTML, CSS, JavaScript
- ☁️ Render.com

---

## 🧠 Funcionalidades Principais
- ✅ Cadastro de músicos para o Ministério de Louvor
- ✅ Gerenciamento de inscrições e audições
- ✅ Criação e edição de usuários administradores
- ✅ Controle de acessos e permissões
- ✅ Página de configurações para abrir ou fechar inscrições
- ✅ Sistema responsivo e com modo escuro

---

## 🔧 Requisitos
- ✔️ Python 3.9 ou superior
- ✔️ Pip
- ✔️ Git (opcional)
- ✔️ Banco de dados:
  - 🗄️ SQLite (local)
  - 🗄️ PostgreSQL (produção)

---

## 📥 Instalação Local
```bash
git clone <seu-repositorio>
cd FORMULARIO_LOUVOR
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate    # Windows
pip install -r requirements.txt
```
Configure o arquivo `config.json` com as credenciais locais.

---

## ▶️ Como Executar
```bash
python app.py
```
O sistema estará disponível em: **http://127.0.0.1:5000**

---

## 📂 Estrutura de Pastas

```
/FORMULARIO_LOUVOR
├── app.py
├── config.json
├── requirements.txt
├── Procfile
├── /static
│   ├── style.css
│   ├── peniel.png
│   └── sarvox_logo.png
├── /templates
│   ├── login.html
│   ├── form.html
│   ├── menu.html
│   ├── gerenciar.html
│   ├── audicoes.html
│   ├── audicoes_gerencia.html
│   ├── audicoes_arquivadas.html
│   ├── detalhes.html
│   ├── editar.html
│   ├── novo_usuario.html
│   ├── editar_usuario.html
│   ├── configuracoes.html
│   ├── senhas.html
│   ├── acesso_negado.html
│   └── sucesso.html
```

---

## 🌐 Principais Rotas Flask

| Rota                      | Função                                         |
|---------------------------|-------------------------------------------------|
| `/`                       | Página de login                                |
| `/menu`                   | Menu principal                                 |
| `/form`                   | Formulário de inscrição                        |
| `/editar`                 | Editar inscrição                               |
| `/inscritos`              | Lista de inscritos                             |
| `/detalhes/<id>`          | Ver detalhes de um inscrito                    |
| `/gerenciar`              | Gerenciar cadastros                            |
| `/audicoes`               | Página pública de inscrições                   |
| `/audicoes_gerencia`      | Gestão de audições                             |
| `/audicoes_arquivadas`    | Histórico de audições                          |
| `/configuracoes`          | Configurações do sistema                       |
| `/novo_usuario`           | Cadastrar novo usuário                         |
| `/editar_usuario/<id>`    | Editar usuários                                |
| `/senhas`                 | Gerenciar senhas                               |
| `/logout`                 | Encerrar sessão                                |

---

## ☁️ Deploy no Render.com

1. Crie um novo serviço **Web Service**.
2. Conecte ao seu repositório GitHub.
3. No campo **Start Command**, utilize:
```bash
gunicorn app:app
```
4. Configure variáveis de ambiente conforme seu `config.json`.
5. Configure banco PostgreSQL via Render.

---

## ⚖️ Licença
Projeto de uso interno da **Igreja Peniel Guilhermina**, permitido uso para fins não comerciais.

---

![Logo Peniel](static/peniel-removebg-preview.png) ![Logo Sarvox](static/sarvox_logo_0_1.png)
