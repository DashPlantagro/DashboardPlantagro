import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
import locale
from conexao_banco_dados import get_connection

# Definir a localização para pt_BR
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Estabelecer a conexão com o banco de dados Oracle
conn = get_connection()

def formatar_para_moeda_brasileira(valor):
    """
    Formata um valor float para o padrão monetário brasileiro manualmente, incluindo o símbolo de Real (R$).
    Exemplo: 1542433.50 se torna 'R$ 1.542.433,50'
    """
    # Primeiro, converte o valor para uma string com duas casas decimais
    valor_str = f"{valor:,.2f}"
    # Substitui pontos por vírgulas e vírgulas por pontos para o formato brasileiro
    valor_str = valor_str.replace(",", "X").replace(".", ",").replace("X", ".")
    # Adiciona o símbolo de Real (R$) no início
    return f"R$ {valor_str}"


def update_chart(start_date, end_date, selected_emp_ids):

    if selected_emp_ids:
        emp_ids_str = ", ".join(f"'{emp_id}'" for emp_id in selected_emp_ids)
        additional_condition = f" AND PDUPPAGA.EMPRESA IN ({emp_ids_str})"
    else:
        additional_condition = ""

    query = f""" 
        SELECT 
            PDUPPAGA.EMPRESA ,
            SUM(PDUPPAGA.VALOR) AS TOTAL_GASTO,
            PEMPRESA.FANTASIA
        FROM 
            PDUPPAGA
        JOIN
            PEMPRESA ON PEMPRESA.EMPRESA = PDUPPAGA.EMPRESA
        JOIN
            PANALITI ON PANALITI.ANALITICA = PDUPPAGA.ANALITICA
        WHERE 
            PDUPPAGA.QUITADA = 'N'
            AND PDUPPAGA.DTEMISSAO BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD')
            AND TO_DATE('{end_date}', 'YYYY-MM-DD')
        {additional_condition}
        AND
            PANALITI.ANALITICA IN (501, 502, 503, 504, 505, 506)
        GROUP BY 
            PDUPPAGA.EMPRESA,PEMPRESA.FANTASIA
        ORDER BY 
            PDUPPAGA.EMPRESA
    """

    df = pd.read_sql(query, conn)

    

    # Adaptação ao tema DARKLY
    df['TOTAL_GASTO_formatado'] = df['TOTAL_GASTO'].apply(formatar_para_moeda_brasileira)

    # Construindo o gráfico com cores apropriadas ao tema DARKLY
    data = [{
        'x': df['FANTASIA'],
        'y': df['TOTAL_GASTO'],
        'type': 'bar',
        'marker': {'color': '#01B8AA'},  # Escolha uma cor que se destaque no fundo escuro
        'name': 'Total de Despesas por Filial',
        'text': df['TOTAL_GASTO_formatado'],
        'hoverinfo': 'text+x'
    }]

    layout = {
        'title': {
            'text': 'Total de Despesas por Filial',
            'font': {'color': 'white'}  # Ajustando a cor do título
        },
        'xaxis': {
            'title': 'Estabelecimento',
            'title_font': {'color': 'white'},  # Ajustes nas cores dos eixos
            'tickfont': {'color': 'white'},    # Cor dos ticks para melhor visibilidade
            'tickangle': -45
        },
        'yaxis': {
            'title': 'Total de Despesas',
            'title_font': {'color': 'white'},  # Ajustes nas cores dos eixos
            'tickfont': {'color': 'white'},    # Cor dos ticks para melhor visibilidade
            'tickformat': ',.2f'
        },
        'paper_bgcolor': '#333',  # Cor de fundo do gráfico adaptada ao tema DARKLY
        'plot_bgcolor': '#333',   # Cor de fundo da área de plotagem adaptada ao tema DARKLY
        'margin': {'l': 50, 'r': 50, 't': 50, 'b': 150},
        'dragmode': False,
        'scrollZoom': False
    }

    return {'data': data, 'layout': layout}