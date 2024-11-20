import streamlit as st
from datetime import datetime, timedelta
from pymongo import MongoClient
from fpdf import FPDF


# Função para criar a conexão com o MongoDB
def criar_conexao():
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client['decio_extintores']
        return db
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None


# Converter datas para datetime
def converter_para_datetime(data):
    if isinstance(data, datetime):
        return data
    return datetime.combine(data, datetime.min.time())


# Função para cadastrar uma empresa
def cadastrar_empresa(nome_empresa, endereco, cidade, extintores, mangueiras, data_cadastro, usuario_cadastrador):
    db = criar_conexao()
    if db is None:
        return
    try:
        # Converter datas
        data_cadastro = converter_para_datetime(data_cadastro)
        for item in extintores:
            item["data_cadastro"] = converter_para_datetime(item["data_cadastro"])
        for item in mangueiras:
            item["data_cadastro"] = converter_para_datetime(item["data_cadastro"])

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


# Função para gerar relatório de vencimento
def gerar_relatorio_vencimento(data_inicio, data_fim):
    db = criar_conexao()
    if db is None:
        return
    usuario_atual = st.session_state['username']
    try:
        # Converter datas
        data_inicio = converter_para_datetime(data_inicio)
        data_fim = converter_para_datetime(data_fim)

        empresas = db.empresas.find({
            "usuario_cadastrador": usuario_atual
        })

        empresas_list = []
        for empresa in empresas:
            extintores_vencendo = [
                extintor for extintor in empresa.get('extintores', [])
                if (extintor['data_cadastro'] + timedelta(days=365)) >= data_inicio and
                   (extintor['data_cadastro'] + timedelta(days=365)) <= data_fim
            ]
            mangueiras_vencendo = [
                mangueira for mangueira in empresa.get('mangueiras', [])
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


# Função para gerar o PDF
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
            f"Data de Cadastro: {empresa['data_cadastro']}"
        )
        pdf.cell(0, 10, linha_empresa, 0, 1)

        if empresa.get('extintores', []):
            pdf.cell(0, 10, "  Extintores Vencendo:", 0, 1)
            for extintor in empresa['extintores']:
                linha_extintor = (
                    f"    Tipo: {extintor['tipo']} | "
                    f"Quantidade: {extintor['quantidade']} | "
                    f"Capacidade: {extintor['capacidade']} | "
                    f"Data de Cadastro: {extintor['data_cadastro']}"
                )
                pdf.cell(0, 10, linha_extintor, 0, 1)

        if empresa.get('mangueiras', []):
            pdf.cell(0, 10, "  Mangueiras Vencendo:", 0, 1)
            for mangueira in empresa['mangueiras']:
                linha_mangueira = (
                    f"    Tamanho: {mangueira['tamanho']}m | "
                    f"Quantidade: {mangueira['quantidade']} | "
                    f"Data de Cadastro: {mangueira['data_cadastro']}"
                )
                pdf.cell(0, 10, linha_mangueira, 0, 1)

    pdf_file = "relatorio_vencimento.pdf"
    pdf.output(pdf_file)
    with open(pdf_file, "rb") as file:
        st.download_button(
            label="Baixar Relatório em PDF",
            data=file,
            file_name=pdf_file,
            mime="application/octet-stream"
        )
    st.success("PDF gerado com sucesso!")


# Tela de Cadastro
def tela_cadastro():
    st.header("Cadastro de Empresa")
    nome_empresa = st.text_input("Nome da Empresa", key="nome_empresa")
    endereco = st.text_input("Endereço", key="endereco")
    cidade = st.text_input("Cidade", key="cidade")
    st.subheader("Cadastro de Extintores")
    lista_tipos_extintores = ["Pó ABC", "Pó BC", "CO2", "Água"]
    lista_capacidades_extintores = ["4kg", "6kg", "8kg", "10kg", "10 Litros"]

    tipo_extintor = st.selectbox("Tipo de Extintor", lista_tipos_extintores)
    capacidade_extintor = st.selectbox("Capacidade", lista_capacidades_extintores)
    quantidade_extintor = st.number_input("Quantidade", min_value=1, value=1)
    data_cadastro_extintor = st.date_input("Data de Cadastro", datetime.now())

    if st.button("Adicionar Extintor"):
        extintor = {
            "tipo": tipo_extintor,
            "capacidade": capacidade_extintor,
            "quantidade": quantidade_extintor,
            "data_cadastro": data_cadastro_extintor
        }
        st.session_state['extintores'].append(extintor)
        st.success("Extintor adicionado com sucesso!")

    st.subheader("Cadastro de Mangueiras")
    lista_tamanhos_mangueiras = [15, 20, 25, 30]
    tamanho_mangueira = st.selectbox("Tamanho (metros)", lista_tamanhos_mangueiras)
    quantidade_mangueira = st.number_input("Quantidade", min_value=1, value=1)
    data_cadastro_mangueira = st.date_input("Data de Cadastro", datetime.now())

    if st.button("Adicionar Mangueira"):
        mangueira = {
            "tamanho": tamanho_mangueira,
            "quantidade": quantidade_mangueira,
            "data_cadastro": data_cadastro_mangueira
        }
        st.session_state['mangueiras'].append(mangueira)
        st.success("Mangueira adicionada com sucesso!")

    st.subheader("Itens Cadastrados")
    st.write("**Extintores**:")
    for extintor in st.session_state['extintores']:
        st.write(extintor)

    st.write("**Mangueiras**:")
    for mangueira in st.session_state['mangueiras']:
        st.write(mangueira)

    if st.button("Cadastrar Empresa"):
        if nome_empresa and endereco and cidade and (st.session_state['extintores'] or st.session_state['mangueiras']):
            cadastrar_empresa(
                nome_empresa, endereco, cidade,
                st.session_state['extintores'],
                st.session_state['mangueiras'],
                datetime.now(),
                st.session_state['username']
            )
        else:
            st.warning("Preencha todos os campos e adicione ao menos um extintor ou mangueira!")
