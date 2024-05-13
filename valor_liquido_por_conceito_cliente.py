import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
import locale
from conexao_banco_dados import get_connection

# Define localização para pt_BR
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Conectar com o banco de dados
conn = get_connection()

def create_layout():
    layout = html.Div(id='container-valor-liquido-conceito', children=[
        dbc.Row([
            dbc.Col(width=1),  # coluna vazia para ocupar espaço à esquerda
            dbc.Col(
                dbc.Card([
                    html.Div([
                        html.H2('Valor Liquido por Conceito de Cliente', style={"font-family": "Voltaire", "font-size": "20px", "text-align": "center", "color": "white"}),
                    ],
                    style={"padding": "10px", "backgroundColor": "#343a40"}  # Ajuste para tema DARKLY
                    ),
                    dbc.Row([
                        dbc.Col([
                            dcc.Graph(
                                id='bar-chart-conceito-pessoa',
                                config={'displayModebar': False}
                            )
                        ])
                    ])
                ], style={"backgroundColor": "#343a40", "border": "1px solid #495057"}),  # Ajuste para tema DARKLY
                width=4
            ),
            dbc.Col(width=1),  # Coluna vazia para ocupar espaço à direita
        ], style={"padding": "20px"})  # Espaço externo para alinhamento
    ], style={"backgroundColor": "#343a40"})  # Ajuste para tema DARKLY
    
    return layout


def update_chart(start_date, end_date, selected_rep_ids,selected_emp_ids,selected_tabpreco_id,selected_cfgpedido_id):

    if selected_tabpreco_id:
        tab_ids_str = ", ".join(f"'{tab_id}'" for tab_id in selected_tabpreco_id)
        additional_condition_tab = f" AND ITEMTABPRC.TABPRC IN ({tab_ids_str})"
    else:
        additional_condition_tab = ""


    if selected_emp_ids:
        emp_ids_str = ", ".join(f"'{emp_id}'" for emp_id in selected_emp_ids)
        additional_condition_emp = f" AND NFCAB.ESTAB IN ({emp_ids_str})"
    else:
        additional_condition_emp = ""

    if selected_rep_ids:
        rep_ids_str = ", ".join(f"'{rep_id}'" for rep_id in selected_rep_ids)
        additional_condition = f" AND PREPRESE.REPRESENT IN ({rep_ids_str})"
    else:
        additional_condition = ""

    if selected_cfgpedido_id:
        cfg_pedido_str = ", ".join(f"'{tab_id}'" for tab_id in selected_cfgpedido_id)
        additional_condition_cfg_ped = f" AND NFCAB.NOTACONF IN ({cfg_pedido_str})"
    else:
        additional_condition_cfg_ped = ""

    query = f"""
    SELECT
        CONCEITO.CONCEITO,
        CONCEITO.DESCRICAO,
        SUM(NFITEM.VALORTOTAL) AS Total_Compras
    FROM
        NFCAB
    LEFT JOIN
        CONTAMOV ON NFCAB.NUMEROCM  = CONTAMOV.NUMEROCM
    LEFT JOIN
        CONCEITOPESSOA ON CONCEITOPESSOA.NUMEROCM = CONTAMOV.NUMEROCM
    LEFT JOIN
        CONCEITO ON CONCEITOPESSOA.CONCEITO = CONCEITO.CONCEITO
    JOIN
        NFCFG ON NFCFG.NOTACONF = NFCAB.NOTACONF
    LEFT JOIN
        PREPRESE ON NFCAB.REPRESENT = PREPRESE.REPRESENT
    LEFT JOIN
            ITEMTABPRC ON ITEMTABPRC.ESTAB = NFCAB.ESTAB AND ITEMTABPRC.TABPRC = NFCAB.TABPRC
    LEFT JOIN
            NFITEM ON NFITEM.SEQNOTA = NFCAB.SEQNOTA AND NFITEM.ESTAB = NFCAB.ESTAB
    WHERE 
         NFCAB.DTEMISSAO BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD') 
            AND TO_DATE('{end_date}', 'YYYY-MM-DD')
            {additional_condition}
            {additional_condition_emp}
            {additional_condition_cfg_ped}
            {additional_condition_tab}
            AND NFCFG.ENTRADASAIDA IN 'S'
        GROUP BY 
            CONCEITO.CONCEITO, 
            CONCEITO.DESCRICAO
        ORDER BY
            TOTAL_COMPRAS DESC
            """
    df = pd.read_sql(query, conn)

    # Inverter a ordem dos dados para que o cliente que mais comprou seja listado primeiro
    df = df[::-1]

    # O DataFrame já está ordenado conforme necessário pela consulta SQL, então não precisamos inverter a ordem
    conceito = df['DESCRICAO'].tolist()

    # Formatando o valor para o formato monetário brasileiro com o símbolo "R$"
    total_compras = [f'R$ {locale.currency(valor, grouping=True, symbol=None)}' for valor in df['TOTAL_COMPRAS']]

    hover_text = [
        f"Conceito: {con}<br>Valor: {val}<br>"
        for con, val in zip(conceito, total_compras)
    ]

    # Retorna a figura para atualizar o gráfico
    return {
        'data': [
            {
                'y': conceito,
                'x': df['TOTAL_COMPRAS'],
                'type': 'bar',
                'orientation': 'h',
                'name': 'Total Compras',
                'hovertemplate': hover_text,
                'text': total_compras,
                'hoverinfo': 'text',
                'marker': {
                    'color': '#17a2b8'  # Cor da barra ajustada para combinar com o tema DARKLY
                },
            }
        ],
        'layout': {
            'title': {
                'text': 'Valor Líquido por Conceito de Clientes',
                'font': {'color': 'white'}
            },
            'plot_bgcolor': '#343a40',
            'paper_bgcolor': '#343a40',
            'font': {'color': 'white'},
            'xaxis': {
                'title': 'Total de Compras',
                'gridcolor': '#495057',
            },
            'yaxis': {
                'title': 'Conceito',
                'tickfont': {'size': 10, 'color': 'white'},
                'gridcolor': '#495057',
            },
            'margin': {'l': 150, 'r': 50, 't': 50, 'b': 50},
            'dragmode': False,
            'scrollZoom': False,
        }
    }