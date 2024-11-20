import streamlit as st
from pymongo import MongoClient
from datetime import datetime


# Função para conectar ao MongoDB usando st.secrets conforme seu modelo
def criar_conexao():
    try:
        client = MongoClient(st.secrets["MONGO_URL"])  # Usando a URL fornecida em secrets.toml
        db = client.extintores  # Nome do banco de dados
        return db
    except Exception as e:
        st.error(f"Erro ao conectar ao MongoDB: {e}")
        return None


# Função para cadastrar a empresa com extintores e mangueiras
def cadastrar_empresa(nome_empresa, endereco, cidade, extintores, mangueiras, data_cadastro, usuario_cadastrador):
    db = criar_conexao()
    if db is None:
        return
    try:
        # Converter a data de cadastro para datetime
        data_cadastro = datetime.combine(data_cadastro, datetime.min.time())

        # Converter as datas dos extintores
        for extintor in extintores:
            extintor["data_cadastro"] = datetime.combine(extintor["data_cadastro"], datetime.min.time())

        # Converter as datas das mangueiras
        for mangueira in mangueiras:
            mangueira["data_cadastro"] = datetime.combine(mangueira["data_cadastro"], datetime.min.time())

        empresa = {
            "nome_empresa": nome_empresa,
            "endereco": endereco,
            "cidade": cidade,
            "extintores": extintores,
            "mangueiras": mangueiras,
            "data_cadastro": data_cadastro,
            "usuario_cadastrador": usuario_cadastrador
        }

        db.empresas.insert_one(empresa)  # Inserir a empresa no banco de dados
        st.success("Empresa cadastrada com sucesso!")
        st.session_state['extintores'] = []
        st.session_state['mangueiras'] = []
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao cadastrar empresa: {e}")


# Função de login
def tela_login():
    st.image('logo.png', width=100)
    st.title("Login Décio Extintores")
    if 'username' not in st.session_state:
        st.session_state['username'] = ''
    username = st.text_input("Usuário", key="username_input")
    senha = st.text_input("Senha", type="password", key="senha_input")
    if st.button("Login"):
        if verificar_usuario(username, senha):  # Verifica o usuário no sistema
            st.session_state['logged_in'] = True
            st.session_state['extintores'] = []
            st.session_state['mangueiras'] = []
            st.session_state['username'] = username
            st.success("Login realizado com sucesso!")
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")


# Função de verificação do usuário
def verificar_usuario(username, senha):
    usuarios_permitidos = {
        st.secrets["USUARIO1"]: st.secrets["SENHA1"],
        st.secrets["USUARIO2"]: st.secrets["SENHA2"]
    }
    return usuarios_permitidos.get(username) == senha


# Função de menu principal
def menu_principal():
    st.sidebar.title("Menu")
    opcao = st.sidebar.selectbox("Escolha uma opção", ["Cadastro de Empresa", "Gerar Relatório de Vencimento",
                                                       "Listar Empresas Cadastradas", "Excluir Empresa"],
                                 key="menu_opcao")
    if opcao == "Cadastro de Empresa":
        tela_cadastro()
    elif opcao == "Gerar Relatório de Vencimento":
        tela_relatorio()
    elif opcao == "Listar Empresas Cadastradas":
        empresas = listar_empresas()  # Chama a função para listar empresas
        if empresas:
            st.header("Empresas Cadastradas")
            st.write(empresas)  # Exibe a lista de empresas
        else:
            st.warning("Nenhuma empresa cadastrada.")
    elif opcao == "Excluir Empresa":
        tela_excluir_empresa()


# Função para listar empresas cadastradas
def listar_empresas():
    db = criar_conexao()
    if db is None:
        return []
    try:
        empresas = db.empresas.find()
        return list(empresas)
    except Exception as e:
        st.error(f"Erro ao listar empresas: {e}")
        return []


# Tela de Cadastro de Empresas
def tela_cadastro():
    st.header("Cadastro de Empresa")
    nome_empresa = st.text_input("Nome da Empresa", key="nome_empresa")
    endereco = st.text_input("Endereço", key="endereco")
    cidade = st.text_input("Cidade", key="cidade")
    st.subheader("Cadastro de Extintores")
    lista_tipos_extintores = ["Pó ABC", "Pó BC", "CÓ2 Dióxido de Carbono", "Água"]
    lista_capacidades_extintores = ["4kg", "6kg", "8kg", "10kg", "10 Litros"]
    tipo_extintor = st.selectbox("Selecione o tipo de extintor", lista_tipos_extintores)
    quantidade_extintor = st.number_input("Quantidade", min_value=1, value=1)
    capacidade_extintor = st.selectbox("Selecione a capacidade", lista_capacidades_extintores)
    data_cadastro_extintor = st.date_input("Data de Cadastro do Extintor", datetime.now())

    tipo_mangueira = st.selectbox("Selecione o tipo de mangueira", [15, 20, 25, 30], index=0)
    quantidade_mangueira = st.number_input("Quantidade de mangueiras", min_value=1, value=1)
    data_cadastro_mangueira = st.date_input("Data de Cadastro da Mangueira", datetime.now())

    # Adiciona extintores
    if st.button("Adicionar Extintor"):
        novo_extintor = {
            "tipo": tipo_extintor,
            "quantidade": quantidade_extintor,
            "capacidade": capacidade_extintor,
            "data_cadastro": data_cadastro_extintor
        }
        st.session_state['extintores'].append(novo_extintor)
        st.success("Extintor adicionado com sucesso!")

    # Adiciona mangueiras
    if st.button("Adicionar Mangueira"):
        nova_mangueira = {
            "tipo": tipo_mangueira,
            "quantidade": quantidade_mangueira,
            "data_cadastro": data_cadastro_mangueira
        }
        st.session_state['mangueiras'].append(nova_mangueira)
        st.success("Mangueira adicionada com sucesso!")

    st.subheader("Lista de Extintores Cadastrados")
    for i, extintor in enumerate(st.session_state.get('extintores', [])):
        st.write(f"Tipo: {extintor['tipo']}, Quantidade: {extintor['quantidade']}, "
                 f"Capacidade: {extintor['capacidade']}, Data de Cadastro: {extintor['data_cadastro']}")
        if st.button(f"Excluir Extintor {i + 1}"):
            st.session_state['extintores'].pop(i)
            st.success("Extintor removido com sucesso.")
            st.rerun()

    st.subheader("Lista de Mangueiras Cadastradas")
    for i, mangueira in enumerate(st.session_state.get('mangueiras', [])):
        st.write(f"Tipo: {mangueira['tipo']} metros, Quantidade: {mangueira['quantidade']}, "
                 f"Data de Cadastro: {mangueira['data_cadastro']}")
        if st.button(f"Excluir Mangueira {i + 1}"):
            st.session_state['mangueiras'].pop(i)
            st.success("Mangueira removida com sucesso.")
            st.rerun()

    if st.button("Cadastrar Empresa"):
        if nome_empresa and endereco and cidade and (
                len(st.session_state.get('extintores', [])) > 0 or len(st.session_state.get('mangueiras', [])) > 0):
            data_cadastro = datetime.now()
            usuario_cadastrador = st.session_state['username']
            cadastrar_empresa(nome_empresa, endereco, cidade, st.session_state['extintores'],
                              st.session_state['mangueiras'], data_cadastro, usuario_cadastrador)
        else:
            st.warning("Por favor, preencha todos os campos e adicione ao menos um extintor ou mangueira.")


# Função para gerar relatório de vencimento (você pode ajustar conforme a sua lógica de vencimento)
def tela_relatorio():
    st.header("Gerar Relatório de Vencimento")
    data_inicio = st.date_input("Data de Início")
    data_fim = st.date_input("Data de Fim")
    if st.button("Gerar Relatório"):
        # Implementar a lógica para gerar o relatório de vencimento
        st.write(f"Gerando relatório de vencimento de {data_inicio} a {data_fim}")


# Função para excluir uma empresa
def tela_excluir_empresa():
    st.header("Excluir Empresa")
    empresas = listar_empresas()
    if empresas:
        nomes_empresas = [empresa['nome_empresa'] for empresa in empresas]
        empresa_para_excluir = st.selectbox("Selecione a empresa para excluir", nomes_empresas)
        if st.button("Excluir Empresa"):
            db = criar_conexao()
            if db is None:
                return
            try:
                resultado = db.empresas.delete_one({"nome_empresa": empresa_para_excluir})
                if resultado.deleted_count > 0:
                    st.success("Empresa excluída com sucesso!")
                else:
                    st.warning("Nenhuma empresa encontrada com o nome selecionado.")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir a empresa: {e}")
    else:
        st.warning("Nenhuma empresa cadastrada.")


# Função principal para o fluxo do app
def main():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if st.session_state['logged_in']:
        menu_principal()
        sair_app()
    else:
        tela_login()


# Função para sair do app
def sair_app():
    if st.button("Sair do App"):
        st.session_state['logged_in'] = False
        st.session_state.pop('username', None)
        st.session_state.pop('extintores', None)
        st.session_state.pop('mangueiras', None)
        st.success("Logout realizado com sucesso!")
        st.rerun()


if __name__ == "__main__":
    main()
