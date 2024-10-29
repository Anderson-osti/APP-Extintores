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


def cadastrar_empresa(nome_empresa, endereco, extintores, data_cadastro, usuario_cadastrador):
    db = criar_conexao()
    if db is None:
        return

    try:
        # Converte a data para o formato ISO antes de armazenar
        data_cadastro_iso = data_cadastro.isoformat()  # Formato: 'YYYY-MM-DD'

        empresa = {
            "nome_empresa": nome_empresa,
            "endereco": endereco,
            "extintores": extintores,
            "data_cadastro": data_cadastro_iso,  # Armazenando como string ISO
            "usuario_cadastrador": usuario_cadastrador  # Adicionando o usuário que cadastrou
        }
        db.empresas.insert_one(empresa)
        st.success("Empresa cadastrada com sucesso!")
        st.rerun()  # Atualiza a página após o cadastro
    except Exception as e:
        st.error(f"Erro ao cadastrar empresa: {e}")


def gerar_relatorio_vencimento(data_inicio, data_fim):
    db = criar_conexao()
    if db is None:
        return

    usuario_atual = st.session_state['username']  # Captura o usuário logado
    try:
        empresas = db.empresas.find({
            "data_cadastro": {"$gte": data_inicio.isoformat(), "$lte": data_fim.isoformat()},
            "usuario_cadastrador": usuario_atual  # Filtrando pelo usuário que cadastrou
        })

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Relatório de Vencimento", ln=True, align='C')

        for empresa in empresas:
            pdf.cell(200, 10, txt=f"Nome: {empresa['nome_empresa']}", ln=True)
            pdf.cell(200, 10, txt=f"Endereço: {empresa['endereco']}", ln=True)
            pdf.cell(200, 10, txt=f"Data de Cadastro: {empresa['data_cadastro']}", ln=True)

            for extintor in empresa.get('extintores', []):
                pdf.cell(200, 10, txt=f"  Tipo: {extintor['tipo']}, Quantidade: {extintor['quantidade']}, "
                                      f"Capacidade: {extintor['capacidade']}", ln=True)

        pdf_file = "relatorio_vencimento.pdf"
        pdf.output(pdf_file)
        st.success("Relatório gerado com sucesso!")
        st.download_button("Baixar Relatório", pdf_file)

    except Exception as e:
        st.error(f"Erro ao gerar relatório: {e}")


def listar_empresas():
    db = criar_conexao()
    if db is None:
        return []

    usuario_atual = st.session_state['username']  # Captura o usuário logado
    try:
        empresas = list(db.empresas.find({"usuario_cadastrador": usuario_atual}))  # Filtrando pelas empresas do usuário
        return empresas
    except Exception as e:
        st.error(f"Erro ao listar empresas: {e}")
        return []


def excluir_empresa(nome_empresa):
    db = criar_conexao()
    if db is None:
        return
    try:
        db.empresas.delete_one({"nome_empresa": nome_empresa})
        st.success(f"Empresa '{nome_empresa}' excluída com sucesso.")
    except Exception as e:
        st.error(f"Erro ao excluir empresa: {e}")


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


def tela_cadastro():
    st.header("Cadastro de Empresa")
    nome_empresa = st.text_input("Nome da Empresa", key="nome_empresa")
    endereco = st.text_input("Endereço", key="endereco")

    # Permitir cadastrar múltiplos tipos de extintores
    st.subheader("Cadastro de Extintores")
    tipos_extintores = []
    extintor_index = 0  # Índice para garantir chaves únicas

    while True:
        # Seleção do tipo de extintor
        tipo_extintor = st.selectbox("Tipo de Extintor", ["Água", "Pó Químico (BC)",
                                                          "Pó Químico (ABC)", "CO2", "Espuma"],
                                     key=f"tipo_extintor_{extintor_index}")

        # Seleção da capacidade do extintor
        capacidade_extintor = st.selectbox("Capacidade do Extintor", ["4 kg", "6 kg", "9 kg", "12 kg", "6 L", "10 L"],
                                           key=f"capacidade_extintor_{extintor_index}")

        quantidade_extintor = st.number_input("Quantidade de Extintores", min_value=1, step=1,
                                              key=f"quantidade_extintor_{extintor_index}")

        # Armazena os dados do extintor
        tipos_extintores.append({
            'tipo': tipo_extintor,
            'quantidade': quantidade_extintor,
            'capacidade': capacidade_extintor
        })

        if st.button("Adicionar outro extintor", key=f"add_extintor_{extintor_index}"):
            extintor_index += 1  # Incrementa o índice para o próximo extintor
            continue
        else:
            break

    data_cadastro = st.date_input("Data de Cadastro", datetime.now(), key="data_cadastro")

    if st.button("Cadastrar Empresa"):
        if nome_empresa and endereco and tipos_extintores:
            usuario_cadastrador = st.session_state['username']  # Captura o usuário logado
            cadastrar_empresa(nome_empresa, endereco, tipos_extintores, data_cadastro, usuario_cadastrador)
        else:
            st.error("Por favor, preencha todos os campos obrigatórios.")


def tela_relatorio():
    st.header("Gerar Relatório de Vencimento")
    data_inicio = st.date_input("Data de Início", datetime.now() - timedelta(days=365), key="data_inicio")
    data_fim = st.date_input("Data de Fim", datetime.now(), key="data_fim")

    if st.button("Gerar Relatório"):
        if data_inicio <= data_fim:
            gerar_relatorio_vencimento(data_inicio, data_fim)
        else:
            st.error("A data de início deve ser anterior à data de fim.")


def sair_app():
    if st.button("Sair do App"):
        st.session_state['logged_in'] = False
        st.session_state.pop('username', None)  # Remove o usuário logado
        st.rerun()  # Reinicia a aplicação


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
                        f"Capacidade: {extintor['capacidade']}"
                    )
        else:
            st.warning("Nenhuma empresa cadastrada.")
    elif opcao == "Excluir Empresa":
        tela_excluir_empresa()


def tela_login():
    st.header("Login")
    username = st.text_input("Usuário", key="username")
    senha = st.text_input("Senha", type="password", key="senha")

    if st.button("Login"):
        if verificar_usuario(username, senha):
            st.session_state['logged_in'] = True
            st.session_state['username'] = username  # Armazena o usuário logado
            st.success("Login realizado com sucesso!")
            st.rerun()  # Atualiza a página após o login
        else:
            st.error("Usuário ou senha inválidos.")


def main():
    st.set_page_config(page_title="Gerenciador de Extintores", layout="wide")
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if st.session_state['logged_in']:
        menu_principal()
        sair_app()
    else:
        tela_login()


if __name__ == "__main__":
    main()
