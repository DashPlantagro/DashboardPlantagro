import pandas as pd
import locale
import plotly.express as px
from conexao_banco_dados import get_connection
from dash import dcc


# Definindo local BR
locale.setlocale(locale.LC_ALL, 'pt-BR.UTF8')

# Conectar BD
conn = get_connection()

def crescimento_cliente():
    query = """
        SELECT DTCADASTRO, NOME  
        FROM PPESCLI
        ORDER BY DTCADASTRO ASC
    """
    df = pd.read_sql(query, conn)
    return df



def create_line_chart(df):
    # Contar o número de clientes por data de cadastro
    df['NUMERO_CLIENTES'] = 1  # Adicionar uma coluna de contagem de 1 para cada cliente
    df['DTCADASTRO'] = pd.to_datetime(df['DTCADASTRO'])  # Certificar-se de que a coluna de data de cadastro é do tipo datetime
    df = df[df['DTCADASTRO'] >= '2019-01-01']  # Filtrar datas a partir de 2020
    df = df.groupby('DTCADASTRO').sum().reset_index()  # Agrupar por data de cadastro e somar as contagens
    
    # Criar o gráfico de linha usando Plotly Express
    fig = px.line(df, x='DTCADASTRO', y='NUMERO_CLIENTES', title='Crescimento da Base de Clientes ao Longo do Tempo')

    # Personalizar o layout do gráfico para o tema darklyn
    fig.update_layout(
        xaxis_title='Data de Cadastro',
        yaxis_title='Quantidade de Clientes Cadastrados no Dia',
        plot_bgcolor='#23272a',  # Cor de fundo da área de plotagem
        paper_bgcolor='#23272a',  # Cor de fundo do papel
        font=dict(color='white'),  # Cor do texto
    )

    # Aumentar o espaço entre as linhas
    fig.update_traces(line=dict(width=2))  # Altera a largura da linha

    return fig



