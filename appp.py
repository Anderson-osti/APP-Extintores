import streamlit as st
from datetime import datetime, timedelta
import pymongo

# Conexão com o banco de dados
def criar_conexao():
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    return client["extintores"]

# Função para cadastrar a empresa
def cadastrar_empresa(nome_empresa, endereco, tipos_extintores, data_cadastro):
    db = criar_conexao()
    if db is None:
        return
    try:
        db.empresas.insert_one({
            "nome_empresa": nome_empresa,
            "endereco": endereco,
            "data_cadastro": data_cadastro,
            "extintores": tipos_extintores,
            "usuario": st.session_state['username']  # Adiciona o usuário responsável
        })
        st.success("Empresa cadastrada com sucesso!")
    except Exception as e:
        st.error(f"Erro ao cadastrar empresa: {e}")

# Função para listar as empresas
def listar_empresas():
    db = criar_conexao()
    if db is None:
        return []
    try:
        usuario_atual = st.session_state['username']  # Captura o usuário logado
        empresas = db.empresas.find({"usuario": usuario_atual})  # Filtra empresas por usuário
        return list(empresas)
    except Exception as e:
        st.error(f"Erro ao listar empresas: {e}")
        return []

# Função para gerar o relatório de vencimento
def gerar_relatorio_vencimento(data_inicio, data_fim):
    db = criar_conexao()
    if db is None:
        return
    try:
        usuario_atual = st.session_state['username']  # Captura o usuário logado
        relatorio = db.empresas.find({
            "usuario": usuario_atual,
            "extintores.data_vencimento": {
                "$gte": data_inicio,
                "$lte": data_fim
            }
        })
        if relatorio:
            st.header("Relatório de Vencimento")
            for empresa in relatorio:
                st.write(f"Empresa: {empresa['nome_empresa']}, Endereço: {empresa['endereco']}")
                for extintor in empresa['extintores']:
                    st.write(f"  Tipo: {extintor['tipo']}, Data de Vencimento: {extintor['data_vencimento']}")
        else:
            st.warning("Nenhuma empresa com vencimentos nesse período.")
    except Exception as e:
        st.error(f"Erro ao gerar relatório: {e}")

# Função para excluir uma empresa
def excluir_empresa(nome_empresa):
    db = criar_conexao()
    if db is None:
        return
    try:
        db.empresas.delete_one({"nome_empresa": nome_empresa})
        st.success(f"Empresa '{nome_empresa}' excluída com sucesso.")
    except Exception as e:
        st.error(f"Erro ao excluir empresa: {e}")

# Função para o login
def tela_login():
    st.header("Login")
    username = st.text_input("Usuário", key="username")
    if st.button("Entrar"):
        if username in ["Anderson", "Décio"]:  # Validação simples
            st.session_state['username'] = username
            st.session_state['logged_in'] = True
            st.success("Login realizado com sucesso!")
            st.experimental_rerun()  # Reinicia a aplicação
        else:
            st.error("Usuário inválido.")

# Função para o logout
def sair_app():
    if st.button("Sair do App"):
        st.session_state['logged_in'] = False
        st.session_state.pop('username', None)  # Remove o usuário logado
        st.rerun()  # Reinicia a aplicação

# Menu principal
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
        if empresas:  # Verifica se existem empresas para exibir
            st.header("Empresas Cadastradas")
            for empresa in empresas:
                st.write(
                    f"Nome: {empresa['nome_empresa']}, Endereço: {empresa['endereco']}, "
                    f"Data de Cadastro: {empresa['data_cadastro']}"
                )

                # Exibe os extintores associados à empresa
                for extintor in empresa.get('extintores', []):
                    st.write(
                        f"  Tipo: {extintor['tipo']}, Quantidade: {extintor['quantidade']}, "
                        f"Capacidade: {extintor['capacidade']}, Data de Vencimento: {extintor['data_vencimento']}"
                    )
        else:
            st.warning("Nenhuma empresa cadastrada.")
    elif opcao == "Excluir Empresa":
        tela_excluir_empresa()

# Função para o cadastro da empresa
def tela_cadastro():
    st.header("Cadastro de Empresa")
    nome_empresa = st.text_input("Nome da Empresa", key="nome_empresa")
    endereco = st.text_input("Endereço", key="endereco")

    # Permitir cadastrar múltiplos tipos de extintores
    st.subheader("Cadastro de Extintores")
    tipos_extintores = []
    extintor_index = 0  # Índice para garantir chaves únicas

    while True:
        tipo_extintor = st.selectbox("Tipo de Extintor", ["Água", "Pó Químico (BC)",
                                                          "Pó Químico (ABC)", "CO2", "Espuma"],
                                     key=f"tipo_extintor_{extintor_index}")
        quantidade_extintor = st.number_input("Quantidade de Extintores", min_value=1, step=1,
                                              key=f"quantidade_extintor_{extintor_index}")
        capacidade_extintor = st.selectbox("Capacidade do Extintor", ["4 kg", "6 kg", "9 kg", "12 kg", "6 L", "10 L"],
                                           key=f"capacidade_extintor_{extintor_index}")
        data_vencimento = st.date_input("Data de Vencimento", key=f"data_vencimento_{extintor_index}")

        # Armazena os dados do extintor
        tipos_extintores.append({
            'tipo': tipo_extintor,
            'quantidade': quantidade_extintor,
            'capacidade': capacidade_extintor,
            'data_vencimento': data_vencimento
        })

        if st.button("Adicionar outro extintor", key=f"add_extintor_{extintor_index}"):
            extintor_index += 1  # Incrementa o índice para o próximo extintor
            continue
        else:
            break

    data_cadastro = st.date_input("Data de Cadastro", datetime.now(), key="data_cadastro")

    if st.button("Cadastrar Empresa"):
        if nome_empresa and endereco:
            cadastrar_empresa(nome_empresa, endereco, tipos_extintores, data_cadastro)
        else:
            st.error("Por favor, preencha todos os campos obrigatórios.")

# Função para gerar relatório de vencimento
def tela_relatorio():
    st.header("Gerar Relatório de Vencimento")
    data_inicio = st.date_input("Data de Início", datetime.now() - timedelta(days=365), key="data_inicio")
    data_fim = st.date_input("Data de Fim", datetime.now(), key="data_fim")

    if st.button("Gerar Relatório"):
        if data_inicio <= data_fim:
            gerar_relatorio_vencimento(data_inicio, data_fim)
        else:
            st.error("A data de início deve ser anterior à data de fim.")

# Função para excluir uma empresa
def tela_excluir_empresa():
    st.header("Excluir Empresa")
    empresas = listar_empresas()

    if not empresas:
        st.warning("Nenhuma empresa cadastrada para excluir.")
        return

    nomes_empresas = [empresa['nome_empresa'] for empresa in empresas]
    nome_empresa = st.selectbox("Selecione a Empresa a ser excluída", nomes_empresas, key="nome_empresa_excluir")

    if st.button("Excluir Empresa"):
        excluir_empresa(nome_empresa)

# Função principal
def main():
    st.set_page_config(page_title="Gerenciador de Extintores", layout="wide")

    # Adicionando a logomarca
    st.image("firecheck/logo.png", width=200)  # Atualize o caminho da imagem conforme necessário

    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if st.session_state['logged_in']:
        menu_principal()
        sair_app()
    else:
        tela_login()

if __name__ == "__main__":
    main()
