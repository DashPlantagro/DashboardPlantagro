import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
import locale
from datetime import datetime
import plotly.graph_objs as go
from conexao_banco_dados import get_connection

# Definir a localização para pt_BR
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Estabelecer a conexão com o banco de dados Oracle
conn = get_connection()

def create_layout():
    layout = html.Div(id='container-grafico-abc-produtos', children=[
        dbc.Row([
            dbc.Col(width=1),  # Coluna vazia para ocupar 1/3 do espaço à esquerda
            dbc.Col(
                dbc.Card([
                    html.Div(
                        [
                            html.H2("Total por Marca de Produto", style={"font-family": "Voltaire", "font-size": "20px", "text-align": "center"}),
                        ],
                        style={"padding": "10px"}  # Adiciona um espaço interno ao div para centralizar o texto
                    ),
                    dbc.Row([
                        dbc.Col([
                            dcc.Graph(
                                id='bar-chart-total-abc-produtos',
                                config={'displayModeBar': False}  # Desabilita a barra de ferramentas (incluindo o zoom pelo mouse)
                            )
                        ])
                    ])
                ]), width=4  # Coluna para ocupar 1/3 do espaço no centro
            ),
            dbc.Col(width=1),  # Coluna vazia para ocupar 1/3 do espaço à direita
        ])
    ])


def update_chart(start_date, end_date, selected_rep_ids, selected_emp_ids, selected_tabpreco_id, selected_cfgpedido_id):
    # Se não receber datas, define um intervalo padrão (exemplo: mês atual)
    if start_date is None or end_date is None:
        end_date = datetime.today().strftime('%Y-%m-%d')
        start_date = (datetime.today() - pd.DateOffset(months=1)).strftime('%Y-%m-%d')

    # Construção das cláusulas de filtro baseadas nas seleções do usuário
    tab_ids_clause = f"AND ITEMTABPRC.TABPRC IN ({', '.join(f"'{tab_id}'" for tab_id in selected_tabpreco_id)})" if selected_tabpreco_id else ""
    emp_ids_clause = f"AND NFCAB.ESTAB IN ({', '.join(f"'{emp_id}'" for emp_id in selected_emp_ids)})" if selected_emp_ids else ""
    cfg_ids_clause = f"AND NFCAB.NOTACONF IN ({', '.join(f"'{cfg_ped}'" for cfg_ped in selected_cfgpedido_id)})" if selected_cfgpedido_id else ""
    rep_ids_clause = f"AND PREPRESE.REPRESENT IN ({', '.join(f"'{rep_id}'" for rep_id in selected_rep_ids)})" if selected_rep_ids else ""

    # Consulta SQL
    query = f"""
    WITH TotalCompras AS (
        SELECT
            COALESCE(SUM(NFITEM.VALORTOTAL), 0) AS TotalCompras
        FROM
            NFCAB
        LEFT JOIN
            NFITEM ON NFITEM.SEQNOTA = NFCAB.SEQNOTA AND NFITEM.ESTAB = NFCAB.ESTAB
        JOIN
            ITEMAGRO ON ITEMAGRO.ITEM = NFITEM.ITEM
        LEFT JOIN
            NFCFG ON NFCFG.NOTACONF = NFCAB.NOTACONF
        LEFT JOIN
            ITEMTABPRC ON ITEMTABPRC.ESTAB = NFCAB.ESTAB AND ITEMTABPRC.TABPRC = NFCAB.TABPRC
        LEFT JOIN
            PREPRESE ON PREPRESE.REPRESENT = NFCAB.REPRESENT
        WHERE
            NFCAB.DTEMISSAO BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD') AND TO_DATE('{end_date}', 'YYYY-MM-DD')
            AND NFCFG.ENTRADASAIDA <> 'S'
            {emp_ids_clause}
            {cfg_ids_clause}
            {tab_ids_clause}            
            {rep_ids_clause}    
    )
    SELECT
        ITEMAGRO.DESCRICAO AS PRODUTO,
        COALESCE(SUM(NFITEM.VALORTOTAL), 0) AS Total_Compras,
        COALESCE(SUM(NFITEM.QUANTIDADE), 0) AS Quantidade_Comprada,
        ROUND((COALESCE(SUM(NFITEM.VALORTOTAL), 0) / (SELECT TotalCompras FROM TotalCompras)) * 100, 2) AS Porcentagem_Compra
    FROM
        NFCAB
    LEFT JOIN
        NFITEM ON NFITEM.SEQNOTA = NFCAB.SEQNOTA AND NFITEM.ESTAB = NFCAB.ESTAB
    JOIN
        ITEMAGRO ON ITEMAGRO.ITEM = NFITEM.ITEM
    LEFT JOIN
        NFCFG ON NFCFG.NOTACONF = NFCAB.NOTACONF
    LEFT JOIN
        ITEMTABPRC ON ITEMTABPRC.ESTAB = NFCAB.ESTAB AND ITEMTABPRC.TABPRC = NFCAB.TABPRC
    LEFT JOIN
        PREPRESE ON PREPRESE.REPRESENT = NFCAB.REPRESENT
    WHERE
        NFCAB.DTEMISSAO BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD') AND TO_DATE('{end_date}', 'YYYY-MM-DD')
        AND NFCFG.ENTRADASAIDA <> 'S'
        {emp_ids_clause}
        {cfg_ids_clause}
        {tab_ids_clause}            
        {rep_ids_clause}        
    GROUP BY
        ITEMAGRO.DESCRICAO
    ORDER BY
        Total_Compras DESC
    """
    # Executa a consulta SQL
    df = pd.read_sql(query, conn)



    # Cálculo da porcentagem acumulada de compras
    df['Total_Acumulado'] = df['TOTAL_COMPRAS'].cumsum()
    # Supondo que 'df' seja seu DataFrame resultante da consulta SQL
    df['Porcentagem_Acumulada'] = df['PORCENTAGEM_COMPRA'].cumsum()


    df = df.head(20)  # Limita a 20 registros

    # Tenta configurar o locale para PT-BR
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    except locale.Error:
        print("Locale pt_BR não disponível. Usando locale padrão.")

    dados_grafico = [
        {
            'x': df['PRODUTO'],  # Categorias no eixo X
            'y': df['TOTAL_COMPRAS'],  # Valores no eixo Y
            'type': 'bar',
            'name': 'Total Compras',
            'text': [f'Produto: {produto}<br>Quantidade: {locale.format_string("%d", quant, grouping=True)}<br>Valor: R$ {locale.format_string("%0.2f", valor, grouping=True)}' 
                    for produto, quant, valor in zip(df['PRODUTO'], df['QUANTIDADE_COMPRADA'], df['TOTAL_COMPRAS'])],
            'hoverinfo': 'text'
        },
        {
            'x': df['PRODUTO'],
            'y': df['PORCENTAGEM_COMPRA'],
            'type': 'scatter',
            'mode': 'lines+markers',
            'line': {'color': 'red', 'dash': 'dash'},
            'name': 'Porcentagem Acumulada',
            'yaxis': 'y2',
            'text': [f'Produto: {produto}<br>Porcentagem de Compra: {locale.format_string("%.2f", porcentagem)}%' 
                    for produto, porcentagem in zip(df['PRODUTO'], df['PORCENTAGEM_COMPRA'])],
            'hoverinfo': 'text'
        }
    ]

    fig_layout = {
        'title': 'Análise ABC de Compras por Produto',
        'xaxis': {'title': 'Produto', 'tickangle': -45},
        'yaxis': {
            'title': 'Total Comprado',
            'side': 'left'
        },
        'yaxis2': {
            'title': 'Porcentagem de Compra',
            'overlaying': 'y',
            'side': 'right',
            'range': [0, 100]  # Ajustando de 0 a 100 por se tratar de uma porcentagem
        },
        'barmode': 'group',
        'plot_bgcolor': '#343a40',
        'paper_bgcolor': '#343a40',
        'font': {'color': 'white'},
        'legend': {'x': 0, 'y': 1},
        'margin': {'l': 150, 'r': 50, 't': 50, 'b': 150}
    }

    return {'data': dados_grafico, 'layout': fig_layout}
