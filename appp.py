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


def cadastrar_empresa(nome_empresa, endereco, extintores, data_cadastro):
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
            "data_cadastro": data_cadastro_iso  # Armazenando como string ISO
        }
        db.empresas.insert_one(empresa)
        st.success("Empresa cadastrada com sucesso!")
    except Exception as e:
        st.error(f"Erro ao cadastrar empresa: {e}")


def gerar_relatorio_vencimento(data_inicio, data_fim):
    db = criar_conexao()
    if db is None:
        return

    try:
        empresas = db.empresas.find({"data_cadastro": {"$gte": data_inicio.isoformat(), "$lte": data_fim.isoformat()}})
        empresas_list = list(empresas)
        if empresas_list:
            st.write("Empresas com extintores próximos do vencimento:")
            for empresa in empresas_list:
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
            gerar_pdf(empresas_list)
        else:
            st.write("Nenhuma empresa com extintores próximos do vencimento.")
    except Exception as e:
        st.error(f"Erro ao gerar relatório: {e}")


def gerar_pdf(empresas):
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, 'Relatório de Vencimento de Extintores', 0, 1, 'C')
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

        def chapter_title(self, title):
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, title, 0, 1, 'L')
            self.ln(5)

        def chapter_body(self, body):
            self.set_font('Arial', '', 12)
            self.multi_cell(0, 10, body)
            self.ln()

    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for empresa in empresas:
        pdf.chapter_title(f"Empresa: {empresa['nome_empresa']}")
        body = (
            f"Endereço: {empresa['endereco']}\n"
            f"Data de Cadastro: {empresa['data_cadastro']}"
        )
        pdf.chapter_body(body)

        for extintor in empresa.get('extintores', []):
            body_extintor = (
                f"  Tipo: {extintor['tipo']}\n"
                f"  Quantidade: {extintor['quantidade']}\n"
                f"  Capacidade: {extintor['capacidade']}\n"
            )
            pdf.chapter_body(body_extintor)

    pdf_file = "relatorio_vencimento.pdf"
    pdf.output(pdf_file)

    with open(pdf_file, "rb") as file:
        btn = st.download_button(
            label="Baixar Relatório em PDF",
            data=file,
            file_name=pdf_file,
            mime="application/octet-stream"
        )
    st.success("PDF gerado com sucesso!")


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


def tela_login():
    st.image('logo.png', width=100)  # Adicionando o logotipo
    st.title("Login FIRECHECK")

    # Widgets para o login
    if 'username' not in st.session_state:
        st.session_state['username'] = ""
    username = st.text_input("Usuário", key="username")
    senha = st.text_input("Senha", type="password", key="senha")

    login_disabled = st.session_state.get("login_disabled", False)

    if st.button("Login", disabled=login_disabled):
        if verificar_usuario(username, senha):
            st.session_state['logged_in'] = True
            st.rerun()  # Usar experimental_rerun para evitar problemas de instância
        else:
            st.error("Usuário ou senha incorretos.")
            st.session_state["login_disabled"] = True  # Desabilitar o botão após falha
    else:
        # Se o usuário já estiver logado, desabilitar o botão
        st.session_state["login_disabled"] = True


def sair_app():
    if st.button("Sair do App"):
        st.session_state['logged_in'] = False
        st.session_state.pop('username', None)  # Remove o usuário logado
        st.session_state["login_disabled"] = False  # Reabilitar o botão de login
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


def tela_cadastro():
    st.header("Cadastro de Empresa")
    nome_empresa = st.text_input("Nome da Empresa", key="nome_empresa")
    endereco = st.text_input("Endereço", key="endereco")

    # Permitir cadastrar múltiplos tipos de extintores
    st.subheader("Cadastro de Extintores")
    tipos_extintores = []
    extintor_index = 0  # Adiciona um índice para cada extintor

    while True:
        tipo_extintor = st.selectbox("Tipo de Extintor", ["Água", "Pó Químico (BC)",
                                                          "Pó Químico (ABC)", "CO2", "Espuma"],
                                     key=f"tipo_extintor_{extintor_index}")
        quantidade_extintor = st.number_input("Quantidade de Extintores", min_value=1, step=1,
                                              key=f"quantidade_extintor_{extintor_index}")
        capacidade_extintor = st.selectbox("Capacidade do Extintor", ["4 kg", "6 kg", "9 kg", "12 kg", "6 L", "10 L"],
                                           key=f"capacidade_extintor_{extintor_index}")

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
        if nome_empresa and endereco:
            cadastrar_empresa(nome_empresa, endereco, tipos_extintores, data_cadastro)
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


if __name__ == "__main__":
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if st.session_state['logged_in']:
        menu_principal()
        sair_app()  # Adiciona o botão de sair
    else:
        tela_login()
