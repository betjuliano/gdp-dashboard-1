import os
import streamlit as st
import pandas as pd
import re

# Caminho correto do arquivo
FILE_PATH = "/workspaces/gdp-dashboard-1/data/h20251.txt"

class StudentAnalyzer:
    def __init__(self):
        self.student = None
        self.courses = pd.DataFrame()
        self.other_courses = pd.DataFrame()
        self.file_path = FILE_PATH  # Define o caminho fixo do arquivo
        self.day_of_week_dict = {}

        # Verifica se o arquivo existe e carrega os dados
        self.load_day_of_week_data()

    def load_day_of_week_data(self):
        """Carrega os dados de dia da semana do arquivo de referência"""
        if not os.path.exists(self.file_path):
            st.error(f"⚠ O arquivo {self.file_path} não foi encontrado!")
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

        # Verifica se o arquivo existe antes de continuar

        data_dir = "data"

        # Cria a pasta 'data' se ela não existir
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        # Caminho do arquivo
        file_path = os.path.join(data_dir, "h20251.txt")

        # Verifica se o arquivo existe antes de continuar
        if not os.path.exists(file_path):
            st.error(f"⚠ O arquivo {file_path} não foi encontrado! Carregue um arquivo válido.")
        else:
            st.success(f"✅ Arquivo {file_path} encontrado com sucesso!")

    def extract_student_info(self, lines):
        """Extrai informações do aluno do texto inserido."""
        student_info = {
            "Nome": "", "Matrícula": "", "Email": "", "Situação": "",
            "Turno": "", "Tempo de curso": "", "Ano Currículo": "", "Período Atual": ""
        }
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            try:
                if "@" in line:
                    student_info["Email"] = line.strip()
                    if i > 0:
                        student_info["Nome"] = lines[i - 1].strip()
                elif "Situação atual" in line:
                    student_info["Situação"] = line.split("(")[0].replace("Situação atual", "").strip()
                elif "Curso" in line:
                    if i + 1 < len(lines):
                        course_line = lines[i + 1].strip()
                        matricula_match = re.search(r'\d{9,}', course_line)
                        if matricula_match:
                            student_info["Matrícula"] = matricula_match.group(0)
                        if "Noturno" in course_line:
                            student_info["Turno"] = "Administração - Noturno"
                        elif "Diurno" in course_line:
                            student_info["Turno"] = "Administração - Diurno"
                elif "Tempo de curso em semestre" in line:
                    if i + 1 < len(lines):
                        tempo_curso_line = lines[i + 1].strip()
                        tempo_curso_match = re.search(r'(\d{1,2})', tempo_curso_line)
                        if tempo_curso_match:
                            student_info["Tempo de curso"] = int(tempo_curso_match.group(1))
                elif "Ano currículo" in line:
                    if i + 1 < len(lines):
                        curriculo_line = lines[i + 1].strip()
                        curriculo_match = re.search(r'(\d{4})', curriculo_line)
                        if curriculo_match:
                            student_info["Ano Currículo"] = curriculo_match.group(1)
                elif "Período Atual" in line:
                    if i + 1 < len(lines):
                        periodo_atual_line = lines[i + 1].strip()
                        periodo_atual_match = re.search(r'^\d{1,2}$', periodo_atual_line)
                        if periodo_atual_match:
                            student_info["Período Atual"] = int(periodo_atual_match.group(0))
            except Exception as e:
                print(f"Erro ao processar linha {i + 1}: '{line}'. Detalhes: {e}")
            finally:
                i += 1
        return student_info

    def extract_courses(self, lines):
        """Extrai as disciplinas obrigatórias do texto inserido."""
        courses = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.isdigit() and 1 <= int(line) <= 10:  # Identifica o início de um semestre
                semester = int(line)
                i += 1
                while i < len(lines) and not lines[i].strip().isdigit() and not lines[i].strip().startswith("Outras disciplinas"):
                    if re.match(r'^[A-Z]{3}\d{4}$', lines[i].strip()):  # Identifica o código da disciplina
                        nome = lines[i - 1].strip()
                        codigo = lines[i].strip()
                        status = lines[i + 1].strip() if i + 1 < len(lines) else "Não Cursada"

                        # Alterando 'Reprovada' para 'Não Cursada'
                        if "Reprovado" in status or "Não cursada" in status:
                            status = "Não Cursada"

                        courses.append({"Código": codigo, "Disciplina": nome, "Semestre": semester, "Status": status})
                        i += 2
                    else:
                        i += 1
            else:
                i += 1

        # Verificação para garantir que disciplinas foram extraídas
        if not courses:
            st.warning("⚠ Nenhuma disciplina obrigatória foi extraída! Verifique o formato dos dados.")

        return courses


    def extract_other_courses(self, lines):
        """Extrai as outras disciplinas do histórico do aluno."""
        other_courses = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if "Outras disciplinas" in line:  # Identifica o início das outras disciplinas
                i += 1
                while i < len(lines) and lines[i].strip():
                    parts = lines[i].strip().split("\t")
                    if len(parts) == 3:  # Formato: Nome da Disciplina \t Código \t Status
                        nome, codigo, status = parts
                        other_courses.append({"Código": codigo, "Disciplina": nome, "Status": status})
                    i += 1
            else:
                i += 1
        return other_courses

    def extract_data(self, text):
        """Extrai informações do aluno e disciplinas"""
        try:
            lines = text.split('\n')
            student_info = self.extract_student_info(lines)
            courses = self.extract_courses(lines)
            other_courses = self.extract_other_courses(lines)
            return student_info, pd.DataFrame(courses), pd.DataFrame(other_courses)
        except Exception as e:
            st.error(f"Erro ao extrair dados: {e}")
            return {}, pd.DataFrame(), pd.DataFrame()

    def process_data(self, raw_data):
        """Processa os dados inseridos pelo usuário."""
        if not raw_data:
            st.error("Erro: Nenhum dado foi inserido.")
            return

        self.student, self.courses, self.other_courses = self.extract_data(raw_data)
        if self.courses.empty and self.other_courses.empty:
            st.error("Erro: Nenhuma disciplina identificada.")
            return

        self.courses['Dia da Semana'] = self.courses['Código'].map(self.day_of_week_dict)
        self.other_courses['Dia da Semana'] = self.other_courses['Código'].map(self.day_of_week_dict)

        # Salvar no session_state
        st.session_state["student"] = self.student
        st.session_state["courses"] = self.courses
        st.session_state["other_courses"] = self.other_courses
        
# Definir a função ANTES de chamá-la
def display_table(df):
    """Exibe a tabela de disciplinas de forma funcional e sem cores."""
    if df.empty:
        st.write("Nenhuma disciplina encontrada.")
        return

    # Exibir o DataFrame sem formatação de cores
    st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    analyzer = StudentAnalyzer()

    # Upload do arquivo de referência, se necessário
    uploaded_file = st.file_uploader("Carregue o arquivo dos horários em formato txt", type="txt")
    if uploaded_file is not None:
        # Garante que o diretório existe antes de salvar o arquivo
        data_dir = os.path.dirname(analyzer.file_path)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        # Agora abre o arquivo para escrita
        with open(analyzer.file_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        
        st.success(f"✅ Arquivo {analyzer.file_path} carregado com sucesso!")

    # Entrada do usuário
    raw_data = st.text_area("Cole os dados do aluno aqui...", height=150, placeholder="Insira os dados do aluno...")

    # Botão de processamento
    if st.button("📊 Processar Dados"):
        analyzer.process_data(raw_data)

    st.divider()

    # Recupera os dados do session_state, se disponíveis
    student = st.session_state.get("student", None)
    courses = st.session_state.get("courses", pd.DataFrame())
    other_courses = st.session_state.get("other_courses", pd.DataFrame())

    if student:
        # Exibir informações do aluno
        st.subheader("📌 Informações do Aluno")
        st.markdown(f"""
        **Nome:** {student.get('Nome', 'N/A')}  
        **Matrícula:** {student.get('Matrícula', 'N/A')}  
        **Email:** {student.get('Email', 'N/A')}  
        **Turno:** {student.get('Turno', 'N/A')}  
        **Tempo de Curso:** {student.get('Tempo de curso', 'N/A')} semestres  
        **Ano Currículo:** {student.get('Ano Currículo', 'N/A')}  
        **Período Atual:** {student.get('Período Atual', 'N/A')}  
        """)

    if not courses.empty:
        # Criando as opções de filtro
        filter_options = ["📚 Todas", "✅ Aprovadas", "❌ Não Cursadas", "🔄 Pares", "🔀 Ímpares", "♻ Resetar"]
        filter_keys = ["all", "aprovadas", "nao_cursadas", "pares", "impares", "all"]

        # Criar uma linha de botões para os filtros
        cols = st.columns(len(filter_options))

        # Se não houver um filtro salvo, definir como "all"
        if "filter_type" not in st.session_state:
            st.session_state["filter_type"] = "all"

        for i, (label, key) in enumerate(zip(filter_options, filter_keys)):
            if cols[i].button(label):
                st.session_state["filter_type"] = key

        # Aplicando o filtro armazenado no session_state
        filter_type = st.session_state["filter_type"]

        # Criar uma cópia do DataFrame original antes de aplicar filtros
        selected_courses = courses.copy()

        # Aplicando os filtros corretamente
        if filter_type == "aprovadas":
            selected_courses = selected_courses[selected_courses["Status"].str.contains("Aprovado|Dispensado", case=False, na=False)]
        elif filter_type == "nao_cursadas":
            selected_courses = selected_courses[selected_courses["Status"].str.contains("Não Cursada", case=False, na=False)]
        elif filter_type == "pares":
            selected_courses = selected_courses[
                selected_courses["Semestre"].notnull() &
                (selected_courses["Semestre"] % 2 == 0) &
                selected_courses["Status"].str.contains("Não Cursada", case=False, na=False)
            ]
        elif filter_type == "impares":
            selected_courses = selected_courses[
                selected_courses["Semestre"].notnull() &
                (selected_courses["Semestre"] % 2 == 1) &
                selected_courses["Status"].str.contains("Não Cursada", case=False, na=False)
            ]
        else:
            selected_courses = courses  # Se "Todas" for selecionado, mostrar todas as disciplinas obrigatórias

        # Exibir as disciplinas apenas quando "Todas" for selecionado
        st.subheader("📘 Disciplinas Obrigatórias" if filter_type == "all" else "📘 Disciplinas Obrigatórias")
        display_table(selected_courses)

    else:
        st.warning("⚠ Nenhuma disciplina obrigatória foi carregada!")

    # Exibir outras disciplinas se houver
    if not other_courses.empty:
        st.subheader("📖 Outras Disciplinas")
        st.dataframe(other_courses)

    # Resumo das disciplinas
    if not courses.empty:
        total_cursadas = courses[courses["Status"].str.contains("Aprovado|Dispensado", case=False, na=False)].shape[0]
        total_nao_cursadas = courses[courses["Status"].str.contains("Reprovado|Não cursada", case=False, na=False)].shape[0]

        st.subheader("📊 Resumo das Disciplinas")
        st.markdown(f"""
        - ✅ **Total Aprovadas:** {total_cursadas}  
        - ❌ **Total Não Cursadas:** {total_nao_cursadas}  
        """)
