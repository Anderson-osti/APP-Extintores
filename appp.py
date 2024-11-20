import streamlit as st
from pymongo import MongoClient
from datetime import datetime, date, timedelta
from fpdf import FPDF
import pandas as pd


# Função para conectar ao MongoDB
def criar_conexao():
    try:
        client = MongoClient(st.secrets["MONGO_URL"])
        db = client.extintores  # Nome do banco de dados
        return db
    except Exception as e:
        st.error(f"Erro ao conectar ao MongoDB: {e}")
        return None


def verificar_usuario(username, senha):
    usuarios_permitidos = {
        st.secrets["USUARIO1"]: st.secrets["SENHA1"],
        st.secrets["USUARIO2"]: st.secrets["SENHA2"]
    }
    return usuarios_permitidos.get(username) == senha


def converter_para_datetime(data):
    """Converte datetime.date para datetime.datetime"""
    if isinstance(data, date):
        return datetime.combine(data, datetime.min.time())  # Converte para datetime com hora 00:00:00
    return data  # Se já for datetime, retorna sem alteração


def cadastrar_empresa(nome_empresa, endereco, cidade, extintores, mangueiras, data_cadastro, usuario_cadastrador):
    db = criar_conexao()
    if db is None:
        return
    try:
        # Converter data_cadastro para datetime se for datetime.date
        data_cadastro = converter_para_datetime(data_cadastro)

        # Converter as datas dos extintores e mangueiras
        for extintor in extintores:
            extintor["data_cadastro"] = converter_para_datetime(extintor["data_cadastro"])
        for mangueira in mangueiras:
            mangueira["data_cadastro"] = converter_para_datetime(mangueira["data_cadastro"])

        empresa = {
            "nome_empresa": nome_empresa,
            "endereco": endereco,
            "cidade": cidade,
            "extintores": extintores,
            "mangueiras": mangueiras,
            "data_cadastro": data_cadastro,
            "usuario_cadastrador": usuario_cadastrador
        }
        db.empresas.insert_one(empresa)
        st.success("Empresa cadastrada com sucesso!")
        st.session_state['extintores'] = []
        st.session_state['mangueiras'] = []
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao cadastrar empresa: {e}")


def gerar_relatorio_vencimento(data_inicio, data_fim):
    db = criar_conexao()
    if db is None:
        return
    usuario_atual = st.session_state['username']
    try:
        # Converter data_inicio e data_fim para datetime se forem datetime.date
        data_inicio = converter_para_datetime(data_inicio)
        data_fim = converter_para_datetime(data_fim)

        empresas = db.empresas.find({
            "usuario_cadastrador": usuario_atual
        })

        empresas_list = []
        for empresa in empresas:
            # Filtrar extintores e mangueiras cujo vencimento está dentro do intervalo selecionado
            extintores_vencendo = [
                extintor for extintor in empresa['extintores']
                if (extintor['data_cadastro'] + timedelta(days=365)) >= data_inicio and
                   (extintor['data_cadastro'] + timedelta(days=365)) <= data_fim
            ]
            mangueiras_vencendo = [
                mangueira for mangueira in empresa['mangueiras']
                if (mangueira['data_cadastro'] + timedelta(days=365)) >= data_inicio and
                   (mangueira['data_cadastro'] + timedelta(days=365)) <= data_fim
            ]

            if extintores_vencendo or mangueiras_vencendo:
                empresas_list.append({
                    "nome_empresa": empresa['nome_empresa'],
                    "endereco": empresa['endereco'],
                    "cidade": empresa.get('cidade', 'N/A'),
                    "data_cadastro": empresa['data_cadastro'],
                    "extintores": extintores_vencendo,
                    "mangueiras": mangueiras_vencendo
                })

        if empresas_list:
            gerar_pdf(empresas_list)
        else:
            st.write("Nenhuma empresa com extintores ou mangueiras vencendo no período selecionado.")
    except Exception as e:
        st.error(f"Erro ao gerar relatório: {e}")


def gerar_pdf(empresas):
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, 'Relatório de Vencimento de Extintores e Mangueiras', 0, 1, 'C')
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for empresa in empresas:
        linha_empresa = (
            f"Empresa: {empresa['nome_empresa']} | "
            f"Endereço: {empresa['endereco']} | "
            f"Cidade: {empresa.get('cidade', 'N/A')} | "
            f"Data de Cadastro: {empresa['data_cadastro']} | "
        )
        pdf.cell(0, 10, linha_empresa, 0, 1)
        for extintor in empresa.get('extintores', []):
            linha_extintor = (
                f"  Tipo: {extintor['tipo']} | "
                f"  Quantidade: {extintor['quantidade']} | "
                f"  Capacidade: {extintor['capacidade']} | "
                f"  Data de Cadastro: {extintor['data_cadastro']} | "
            )
            pdf.cell(0, 10, linha_extintor, 0, 1)
        for mangueira in empresa.get('mangueiras', []):
            linha_mangueira = (
                f"  Tipo: {mangueira['tipo']} | "
                f"  Quantidade: {mangueira['quantidade']} | "
                f"  Comprimento: {mangueira['comprimento']} | "
                f"  Data de Cadastro: {mangueira['data_cadastro']} | "
            )
            pdf.cell(0, 10, linha_mangueira, 0, 1)
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


def listar_empresas(data_inicio, data_fim):
    db = criar_conexao()
    if db is None:
        return []

    usuario_atual = st.session_state['username']
    try:
        empresas = db.empresas.find({"usuario_cadastrador": usuario_atual})
        empresas_list = list(empresas)

        # Exibe as empresas em formato de tabela interativa
        df = pd.DataFrame(empresas_list)

        # Remove qualquer coluna desnecessária (como ObjectId se existir)
        if '_id' in df.columns:
            df = df.drop(columns=['_id'])

        # Exibe apenas a tabela
        st.dataframe(df)  # Exibe a tabela de empresas

        return empresas_list
    except Exception as e:
        st.error(f"Erro ao listar empresas: {e}")
        return []


def tela_login():
    st.image('logo.png', width=100)
    st.title("Login Décio Extintores")
    if 'username' not in st.session_state:
        st.session_state['username'] = ''
    username = st.text_input("Usuário", key="username_input")
    senha = st.text_input("Senha", type="password", key="senha_input")
    if st.button("Login"):
        if verificar_usuario(username, senha):
            st.session_state['logged_in'] = True
            st.session_state['extintores'] = []
            st.session_state['mangueiras'] = []
            st.session_state['username'] = username
            st.success("Login realizado com sucesso!")
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")


def sair_app():
    if st.button("Sair do App"):
        st.session_state['logged_in'] = False
        st.session_state.pop('username', None)
        st.session_state.pop('extintores', None)
        st.session_state.pop('mangueiras', None)
        st.success("Logout realizado com sucesso!")
        st.rerun()


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
        data_inicio = st.date_input("Data de Início", value=datetime.now())
        data_fim = st.date_input("Data de Fim", value=datetime.now())
        empresas = listar_empresas(data_inicio=data_inicio, data_fim=data_fim)  # Passando as datas para o filtro
        if empresas:
            st.header("Empresas Cadastradas")
            for empresa in empresas:
                st.write(f"Nome: {empresa['nome_empresa']}, Endereço: {empresa['endereco']}, "
                         f"Cidade: {empresa['cidade']}, Data de Cadastro: {empresa['data_cadastro']}, "
                         f"Extintores: {empresa['quantidade_extintores']}, "
                         f"Mangueiras: {empresa['quantidade_mangueiras']}")
        else:
            st.warning("Nenhuma empresa cadastrada.")
    elif opcao == "Excluir Empresa":
        tela_excluir_empresa()

    sair_app()  # Adicionando a função de logout no menu


def tela_cadastro():
    st.header("Cadastro de Empresa")
    nome_empresa = st.text_input("Nome da Empresa")
    endereco = st.text_input("Endereço")
    cidade = st.text_input("Cidade")
    data_cadastro = st.date_input("Data de Cadastro", value=datetime.now())

    # Cadastro de extintores
    st.subheader("Cadastro de Extintores")
    extintores = []
    while True:
        tipo_extintor = st.text_input("Tipo de Extintor")
        quantidade = st.number_input("Quantidade de Extintores", min_value=1)
        capacidade = st.number_input("Capacidade do Extintor", min_value=1)
        data_cadastro_extintor = st.date_input("Data de Cadastro do Extintor", value=datetime.now())
        if st.button("Adicionar Extintor"):
            extintores.append({
                "tipo": tipo_extintor,
                "quantidade": quantidade,
                "capacidade": capacidade,
                "data_cadastro": data_cadastro_extintor
            })
        if len(extintores) > 0:
            st.write("Extintores cadastrados:", extintores)

    # Cadastro de mangueiras
    st.subheader("Cadastro de Mangueiras")
    mangueiras = []
    while True:
        tipo_mangueira = st.selectbox("Tipo de Mangueira", ["15 metros", "20 metros", "25 metros", "30 metros"])
        quantidade_mangueira = st.number_input("Quantidade de Mangueiras", min_value=1)
        data_cadastro_mangueira = st.date_input("Data de Cadastro da Mangueira", value=datetime.now())
        if st.button("Adicionar Mangueira"):
            mangueiras.append({
                "tipo": tipo_mangueira,
                "quantidade": quantidade_mangueira,
                "data_cadastro": data_cadastro_mangueira
            })
        if len(mangueiras) > 0:
            st.write("Mangueiras cadastradas:", mangueiras)

    # Finalizando cadastro da empresa
    if st.button("Cadastrar Empresa"):
        cadastrar_empresa(nome_empresa, endereco, cidade, extintores, mangueiras, data_cadastro, st.session_state['username'])


def tela_relatorio():
    st.header("Gerar Relatório de Vencimento")
    data_inicio = st.date_input("Data de Início")
    data_fim = st.date_input("Data de Fim")
    if st.button("Gerar Relatório"):
        gerar_relatorio_vencimento(data_inicio, data_fim)


def tela_excluir_empresa():
    st.header("Excluir Empresa")
    empresas = listar_empresas(datetime.now(), datetime.now())
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


def main():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if st.session_state['logged_in']:
        menu_principal()
    else:
        tela_login()


if __name__ == "__main__":
    main()
