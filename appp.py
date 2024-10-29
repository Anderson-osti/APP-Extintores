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


def cadastrar_empresa(nome_empresa, endereco, extintores):
    db = criar_conexao()
    if db is None:
        return

    try:
        # Converte a data para o formato ISO antes de armazenar
        data_cadastro_iso = datetime.now().isoformat()  # Formato: 'YYYY-MM-DD'

        empresa = {
            "nome_empresa": nome_empresa,
            "endereco": endereco,
            "extintores": extintores,
            "data_cadastro": data_cadastro_iso,
            "usuario": st.session_state['username']  # Armazena o usuário que cadastrou
        }
        db.empresas.insert_one(empresa)
        st.success("Empresa cadastrada com sucesso!")
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
            "usuario": usuario_atual  # Filtra pelo usuário atual
        })
        empresas_list = list(empresas)
        if empresas_list:
            st.write("Empresas com extintores próximos do vencimento:")
            for empresa in empresas_list:
                st.write(
                    f"Nome: {empresa['nome_empresa']}, "
                    f"Data de Cadastro: {empresa['data_cadastro']}"
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
            f"Data de Cadastro: {empresa['data_cadastro']}\n"
        )
        pdf.chapter_body(body)

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
        empresas = db.empresas.find({"usuario": usuario_atual})  # Filtra as empresas do usuário
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

    if st.button("Login"):
        if verificar_usuario(username, senha):
            st.session_state['logged_in'] = True
            st.rerun()  # Reinicia a aplicação para carregar o menu principal
        else:
            st.error("Usuário ou senha incorretos.")


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
        else:
            st.warning("Nenhuma empresa cadastrada.")
    elif opcao == "Excluir Empresa":
        tela_excluir_empresa()


def tela_cadastro():
    st.header("Cadastro de Empresa")
    nome_empresa = st.text_input("Nome da Empresa", key="nome_empresa")
    endereco = st.text_input("Endereço", key="endereco")

    # Inicializa o estado para armazenar extintores se não existir
    if 'tipos_extintores' not in st.session_state:
        st.session_state['tipos_extintores'] = []

    # Permitir cadastrar múltiplos tipos de extintores
    st.subheader("Cadastro de Extintores")

    if st.session_state['tipos_extintores']:
        for i, extintor in enumerate(st.session_state['tipos_extintores']):
            st.write(f"Extintor {i + 1}: Tipo: {extintor['tipo']}, Quantidade: {extintor['quantidade']}, Capacidade: {extintor['capacidade']}")
            if st.button(f"Remover Extintor {i + 1}", key=f"remove_extintor_{i}"):
                st.session_state['tipos_extintores'].pop(i)  # Remove o extintor da lista
                st.experimental_rerun()  # Atualiza a página para refletir a remoção

    # Adicionar novo extintor
    tipo_extintor = st.selectbox("Tipo de Extintor", ["Água", "Pó Químico (BC)",
                                                      "Pó Químico (ABC)", "CO2", "Espuma"],
                                 key="novo_tipo_extintor")
    quantidade_extintor = st.number_input("Quantidade de Extintores", min_value=1, step=1,
                                          key="nova_quantidade_extintor")
    capacidade_extintor = st.selectbox("Capacidade do Extintor", ["4 kg", "6 kg", "9 kg", "12 kg", "6 L", "10 L"],
                                       key="nova_capacidade_extintor")

    if st.button("Adicionar Extintor"):
        # Adiciona os dados atuais à lista de extintores
        st.session_state['tipos_extintores'].append({
            'tipo': tipo_extintor,
            'quantidade': quantidade_extintor,
            'capacidade': capacidade_extintor
        })
        st.experimental_rerun()  # Atualiza a página para refletir a adição

    if st.button("Cadastrar Empresa"):
        # Verifica se existem extintores antes de cadastrar a empresa
        if st.session_state['tipos_extintores']:
            cadastrar_empresa(nome_empresa, endereco, st.session_state['tipos_extintores'])
            st.session_state['tipos_extintores'] = []  # Limpa a lista de extintores após o cadastro
        else:
            st.warning("Adicione pelo menos um extintor antes de cadastrar a empresa.")


def tela_relatorio():
    st.header("Gerar Relatório de Vencimento")
    data_inicio = st.date_input("Data de Início", datetime.now() - timedelta(days=30))
    data_fim = st.date_input("Data de Fim", datetime.now())

    if st.button("Gerar Relatório"):
        gerar_relatorio_vencimento(data_inicio, data_fim)


def tela_excluir_empresa():
    st.header("Excluir Empresa")
    empresas = listar_empresas()  # Chama a função para listar empresas
    if empresas:  # Verifica se existem empresas para exibir
        nome_empresa_para_excluir = st.selectbox("Escolha a empresa para excluir", [empresa['nome_empresa'] for empresa in empresas])

        if st.button("Excluir Empresa"):
            db = criar_conexao()
            if db is not None:
                try:
                    db.empresas.delete_one({"nome_empresa": nome_empresa_para_excluir, "usuario": st.session_state['username']})
                    st.success("Empresa excluída com sucesso!")
                    st.experimental_rerun()  # Atualiza a página para refletir a exclusão
                except Exception as e:
                    st.error(f"Erro ao excluir a empresa: {e}")
    else:
        st.warning("Nenhuma empresa cadastrada para excluir.")


def main():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if st.session_state['logged_in']:
        menu_principal()
        sair_app()  # Botão para sair do app
    else:
        tela_login()


if __name__ == "__main__":
    main()
