import os
import streamlit as st
import pandas as pd
import re
import tempfile

# --------------------- LOGIN SYSTEM --------------------- #

# Lista de usuários e senhas (pode ser substituído por um banco de dados)
USERS = {
    "Juliano": "0510",
    "Eliete": "4125"
}

# Inicializa o estado da sessão para login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Tela de Login
if not st.session_state.logged_in:
    st.title("🔒 Faça seu login de coordenação")

    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if username in USERS and USERS[username] == password:
            st.session_state.logged_in = True
            st.success("✅ Login bem-sucedido!")
            st.rerun()  # Atualiza a página para exibir o app
        else:
            st.error("❌ Usuário ou senha incorretos!")

    # Para evitar que o resto do app seja exibido
    st.stop()  # ⛔ Para a execução aqui se não estiver logado!

# --------------------- APP COMEÇA AQUI --------------------- #

st.title("📚 Histórico Acadêmico - UFSM")

# Exibir um rodapé menor
st.markdown(
    '<p style="font-size: 10px; font-weight: normal;">Desenvolvido por Juliano Alves. Clique em "Sair" para fechar.</p>',
    unsafe_allow_html=True
)

# Botão de saída que encerra o Streamlit
if st.button("🚪 Sair"):
    st.session_state.logged_in = False
    st.session_state.clear()
    st.rerun()  # Reinicia a aplicação ao deslogar


# --------------------- CLASS STUDENT ANALYZER --------------------- #

class StudentAnalyzer:
    def __init__(self):
        self.student = None
        self.courses = pd.DataFrame()
        self.other_courses = pd.DataFrame()
        self.file_path = os.path.join(tempfile.gettempdir(), "h20251.txt")  # Usa um diretório temporário
        self.day_of_week_dict = {}

        # Verifica se o arquivo existe e carrega os dados
        self.load_day_of_week_data()

    def load_day_of_week_data(self):
        """Carrega os dados de dia da semana do arquivo de referência"""
        if not os.path.exists(self.file_path):
            st.warning(f"⚠ O arquivo {self.file_path} não foi encontrado! Faça o upload abaixo.")
            return

        try:
            day_of_week_df = pd.read_csv(
                self.file_path,
                sep=r'\s{2,}|\t',
                engine='python',
                header=None,
                names=['Código', 'Dia da Semana'],
                dtype=str
            )
            day_of_week_df = day_of_week_df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
            day_of_week_df = day_of_week_df[day_of_week_df['Código'] != 'Código']
            self.day_of_week_dict = pd.Series(day_of_week_df['Dia da Semana'].values, index=day_of_week_df['Código']).to_dict()
        except Exception as e:
            st.error(f"Erro ao carregar o arquivo: {e}")

    def process_data(self, raw_data):
        """Processa os dados inseridos pelo usuário."""
        if not raw_data:
            st.error("Erro: Nenhum dado foi inserido.")
            return

        # Simulação de processamento de dados
        self.student = {"Nome": "Aluno Teste", "Matrícula": "123456789"}
        self.courses = pd.DataFrame({
            "Código": ["ADM101", "ADM102"],
            "Disciplina": ["Gestão", "Estratégia"],
            "Status": ["Aprovado", "Não Cursada"]
        })
        self.other_courses = pd.DataFrame({
            "Código": ["ECO201"],
            "Disciplina": ["Economia"],
            "Status": ["Aprovado"]
        })

        # Verifica se os DataFrames contêm a coluna "Código" antes de mapear
        if not self.courses.empty and "Código" in self.courses.columns:
            self.courses["Dia da Semana"] = self.courses["Código"].map(self.day_of_week_dict)

        if not self.other_courses.empty and "Código" in self.other_courses.columns:
            self.other_courses["Dia da Semana"] = self.other_courses["Código"].map(self.day_of_week_dict)

        # Salvar no session_state
        st.session_state["student"] = self.student
        st.session_state["courses"] = self.courses
        st.session_state["other_courses"] = self.other_courses


# Criar a instância do analisador
analyzer = StudentAnalyzer()

# --------------------- UPLOAD DO ARQUIVO --------------------- #

uploaded_file = st.file_uploader("Carregue o arquivo dos horários em formato txt", type="txt")

if uploaded_file is not None:
    # Salvar o arquivo no diretório temporário
    analyzer.file_path = os.path.join(tempfile.gettempdir(), "h20251.txt")

    with open(analyzer.file_path, "wb") as f:
        f.write(uploaded_file.getvalue())

    st.success(f"✅ Arquivo carregado com sucesso!")
    analyzer.load_day_of_week_data()  # Recarrega os dados após upload

# --------------------- ENTRADA DO USUÁRIO --------------------- #

raw_data = st.text_area("Cole os dados do aluno aqui...", height=150, placeholder="Insira os dados do aluno...")

if st.button("📊 Processar Dados"):
    analyzer.process_data(raw_data)

st.divider()

# --------------------- EXIBIÇÃO DOS DADOS --------------------- #

student = st.session_state.get("student", None)
courses = st.session_state.get("courses", pd.DataFrame())
other_courses = st.session_state.get("other_courses", pd.DataFrame())

if student:
    st.subheader("📌 Informações do Aluno")
    st.markdown(f"""
    **Nome:** {student.get('Nome', 'N/A')}  
    **Matrícula:** {student.get('Matrícula', 'N/A')}  
    """)

if not courses.empty:
    st.subheader("📘 Disciplinas Obrigatórias")
    st.dataframe(courses)

if not other_courses.empty:
    st.subheader("📖 Outras Disciplinas")
    st.dataframe(other_courses)
