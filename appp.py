import streamlit as st
from pymongo import MongoClient
from datetime import datetime
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
            "usuario_cadastrador": usuario_atual  # Filtra pelo usuário
        })
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

    usuario_atual = st.session_state['username']  # Captura o usuário logado
    try:
        empresas = db.empresas.find({"usuario_cadastrador": usuario_atual})  # Filtra empresas pelo usuário
        return list(empresas)
    except Exception as e:
        st.error(f"Erro ao listar empresas: {e}")
        return []


def tela_login():
    st.image('logo.png', width=100)  # Adicionando o logotipo
    st.title("Login Décio Extintores")

    # Widgets para o login
    if 'username' not in st.session_state:  # Verifica se o 'username' já está no session_state
        st.session_state['username'] = ''  # Inicializa o 'username' como string vazia

    username = st.text_input("Usuário", key="username_input")
    senha = st.text_input("Senha", type="password", key="senha_input")

    if st.button("Login"):
        if verificar_usuario(username, senha):
            st.session_state['logged_in'] = True
            st.session_state['extintores'] = []  # Limpa a lista de extintores na sessão
            st.session_state['username'] = username  # Armazena o usuário logado
            st.success("Login realizado com sucesso!")
            st.rerun()  # Atualiza a página após o login
        else:
            st.error("Usuário ou senha incorretos.")


def sair_app():
    if st.button("Sair do App"):
        st.session_state['logged_in'] = False
        st.session_state.pop('username', None)  # Remove o usuário logado
        st.session_state.pop('extintores', None)  # Remove a lista de extintores
        st.success("Logout realizado com sucesso!")
        st.rerun()  # Atualiza a página após o logout


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
        else:
            st.warning("Nenhuma empresa cadastrada.")
    elif opcao == "Excluir Empresa":
        tela_excluir_empresa()


def tela_cadastro():
    st.header("Cadastro de Empresa")
    nome_empresa = st.text_input("Nome da Empresa", key="nome_empresa")
    endereco = st.text_input("Endereço", key="endereco")

    # Permitir cadastrar apenas um tipo de extintor
    st.subheader("Cadastro de Extintores")

    # Listas de tipos de extintores e capacidades
    lista_tipos_extintores = ["Pó ABC", "Pó BC", "CÓ2 Dióxido de Carbono", "Água"]
    lista_capacidades_extintores = [4.0, 6.0, 8.0, 9.0, 10.0, 12.0]

    # Campos para adicionar um extintor
    tipo_extintor = st.selectbox("Selecione o tipo de extintor", lista_tipos_extintores)
    quantidade_extintor = st.number_input("Quantidade", min_value=1, step=1)
    capacidade_extintor = st.selectbox("Selecione a capacidade (litros)", lista_capacidades_extintores)

    if st.button("Cadastrar Extintor"):
        # Cria a lista de extintores apenas se ainda não existir
        if 'extintores' not in st.session_state:
            st.session_state['extintores'] = []

        # Adiciona um extintor à lista
        novo_extintor = {"tipo": tipo_extintor, "quantidade": quantidade_extintor, "capacidade": capacidade_extintor}
        st.session_state['extintores'].append(novo_extintor)
        st.success("Extintor adicionado com sucesso!")

    st.subheader("Lista de Extintores Cadastrados")
    for extintor in st.session_state.get('extintores', []):
        st.write(
            f"Tipo: {extintor['tipo']}, Quantidade: {extintor['quantidade']}, Capacidade: {extintor['capacidade']}")

    if st.button("Cadastrar Empresa"):
        if nome_empresa and endereco and st.session_state.get('extintores'):  # Verifica se há extintores cadastrados
            data_cadastro = datetime.now()
            usuario_cadastrador = st.session_state['username']
            cadastrar_empresa(nome_empresa, endereco, st.session_state['extintores'], data_cadastro,
                              usuario_cadastrador)
        else:
            st.warning("Por favor, preencha todos os campos e adicione um extintor.")


def tela_relatorio():
    st.header("Gerar Relatório de Vencimento")
    data_inicio = st.date_input("Data de Início")
    data_fim = st.date_input("Data de Fim")

    if st.button("Gerar Relatório"):
        gerar_relatorio_vencimento(data_inicio, data_fim)


def tela_excluir_empresa():
    st.header("Excluir Empresa")
    empresas = listar_empresas()
    if empresas:
        # Cria uma lista com os nomes das empresas para o selectbox
        nomes_empresas = [empresa['nome_empresa'] for empresa in empresas]
        empresa_para_excluir = st.selectbox("Selecione a empresa para excluir", nomes_empresas)

        if st.button("Excluir Empresa"):
            db = criar_conexao()
            if db is None:
                return

            # Remove a empresa selecionada
            try:
                resultado = db.empresas.delete_one({"nome_empresa": empresa_para_excluir})
                if resultado.deleted_count > 0:
                    st.success("Empresa excluída com sucesso!")
                else:
                    st.warning("Nenhuma empresa encontrada com o nome selecionado.")
                st.rerun()  # Atualiza a página após a exclusão
            except Exception as e:
                st.error(f"Erro ao excluir a empresa: {e}")
    else:
        st.warning("Nenhuma empresa cadastrada.")


# Main
def main():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if st.session_state['logged_in']:
        menu_principal()
        sair_app()
    else:
        tela_login()


if __name__ == "__main__":
    main()
