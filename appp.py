import streamlit as st
from pymongo import MongoClient
from datetime import datetime, timedelta
from fpdf import FPDF

# Conectar ao MongoDB
def criar_conexao():
    try:
        client = MongoClient(st.secrets["MONGO_URL"])
        db = client.extintores  # Nome do banco de dados
        return db
    except Exception as e:
        st.error(f"Erro ao conectar ao MongoDB: {e}")
        return None

def verificar_usuario(username, senha):
    # Usuários permitidos
    usuarios_permitidos = {
        st.secrets["USUARIO1"]: st.secrets["SENHA1"],
        st.secrets["USUARIO2"]: st.secrets["SENHA2"]
    }
    return usuarios_permitidos.get(username) == senha

def cadastrar_empresa(nome_empresa, endereco, tipo_extintor, quantidade_extintor, capacidade_extintor, data_cadastro):
    db = criar_conexao()
    if db is None:
        return

    try:
        empresa = {
            "nome_empresa": nome_empresa,
            "endereco": endereco,
            "tipo_extintor": tipo_extintor,
            "quantidade_extintor": quantidade_extintor,
            "capacidade_extintor": capacidade_extintor,
            "data_cadastro": data_cadastro.strftime('%Y-%m-%d')  # Convertendo para string
        }
        db.empresas.insert_one(empresa)
        st.success("Empresa cadastrada com sucesso!")
    except Exception as e:
        st.error(f"Erro ao cadastrar empresa: {e}")

def listar_empresas():
    db = criar_conexao()
    if db is None:
        return []

    try:
        empresas = db.empresas.find()
        empresas_list = list(empresas)
        st.write("Empresas Cadastradas:", empresas_list)  # Mostra o conteúdo retornado
        return empresas_list
    except Exception as e:
        st.error(f"Erro ao listar empresas: {e}")
        return []

def tela_login():
    st.image('logo.png', width=100)  # Adicionando o logotipo
    st.title("Login no Meu App")
    username = st.text_input("Usuário", key="username")
    senha = st.text_input("Senha", type="password", key="senha")

    if st.button("Login"):
        if verificar_usuario(username, senha):
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")

def tela_cadastro():
    st.header("Cadastro de Empresa")
    nome_empresa = st.text_input("Nome da Empresa", key="nome_empresa")
    endereco = st.text_input("Endereço", key="endereco")
    tipo_extintor = st.selectbox("Tipo de Extintor", ["Água", "Pó Químico (BC)", "Pó Químico (ABC)", "CO2", "Espuma"],
                                 key="tipo_extintor")
    quantidade_extintor = st.number_input("Quantidade de Extintores", min_value=1, step=1, key="quantidade_extintor")
    capacidade_extintor = st.selectbox("Capacidade do Extintor", ["4 kg", "6 kg", "9 kg", "12 kg", "6 L", "10 L"],
                                       key="capacidade_extintor")
    data_cadastro = st.date_input("Data de Cadastro", datetime.now(), key="data_cadastro")

    if st.button("Cadastrar Empresa"):
        if nome_empresa and endereco:
            cadastrar_empresa(nome_empresa, endereco, tipo_extintor, quantidade_extintor, capacidade_extintor,
                              data_cadastro)
        else:
            st.error("Por favor, preencha todos os campos obrigatórios.")

def menu_principal():
    st.sidebar.title("Menu")
    opcao = st.sidebar.selectbox("Escolha uma opção",
                                 ["Cadastro de Empresa", "Listar Empresas Cadastradas"], key="menu_opcao")

    if opcao == "Cadastro de Empresa":
        tela_cadastro()
    elif opcao == "Listar Empresas Cadastradas":
        empresas = listar_empresas()
        if empresas:
            for empresa in empresas:
                st.write(f"Nome: {empresa['nome_empresa']}, Endereço: {empresa['endereco']}")
        else:
            st.warning("Nenhuma empresa cadastrada.")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if st.session_state['logged_in']:
    menu_principal()
else:
    tela_login()
