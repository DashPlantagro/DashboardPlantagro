import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
import locale
from conexao_banco_dados import get_connection

# Define o local BR
locale.setlocale(locale.LC_ALL, 'pt-BR.UTF8')

# Conectar BD
conn = get_connection()

def create_layout():
    layout = html.Div(id='container-valor-liquido-por-produto', children=[
        dbc.Row([
            dbc.Col(width=1),  # Margem esquerda
            dbc.Col(
                dbc.Card([
                    html.Div([
                        html.H2('Valor Líquido por Produto', style={"font-family": "Voltaire", "font-size": "20px", "text-align": "center", "color": "white"}),
                    ],
                    style={"padding": "10px", "backgroundColor": "#343a40"}  # Ajuste para o tema DARKLY
                    ),
                    dbc.Row([
                        dbc.Col([
                            dcc.Graph(
                                id='bar-chart-valor-liquido-por-produto',
                                config={'displayModeBar': False}
                            )
                        ])
                    ])
                ], style={"backgroundColor": "#343a40", "border": "1px solid #495057"}),  # Ajuste para o tema DARKLY
                width=10  # Ajuste na largura para melhor visualização
            ),
            dbc.Col(width=1),  # Margem direita
        ], style={"padding": "20px"})  # Ajuste no espaçamento
    ], style={"backgroundColor": "#343a40"})  # Fundo do container ajustado para o tema DARKLY
    
    return layout


def update_chart(start_date, end_date, selected_reps_ids,selected_emp_ids,selected_tabpreco_id,selected_cfgpedido_id):

    if selected_tabpreco_id:
        tab_ids_str = ", ".join(f"'{tab_id}'" for tab_id in selected_tabpreco_id)
        additional_condition_tab = f" AND ITEMTABPRC.TABPRC IN ({tab_ids_str})"
    else:
        additional_condition_tab = ""


    if selected_emp_ids:
        emp_ids_str = ", ".join(f"'{emp_id}'" for emp_id in selected_emp_ids)
        additional_condition_emp = f" AND PEDCAB.ESTAB IN ({emp_ids_str})"
    else:
        additional_condition_emp = ""

    if selected_reps_ids:
        reps_ids_str = ", ".join(f"'{rep_id}'" for rep_id in selected_reps_ids)
        additional_condition = f" AND PREPRESE.REPRESENT IN ({reps_ids_str})"
    else:
        additional_condition = ""

    if selected_cfgpedido_id:
        cfg_pedido_str = ", ".join(f"'{tab_id}'" for tab_id in selected_cfgpedido_id)
        additional_condition_cfg_ped = f" AND PEDCFG.PEDIDOCONF IN ({cfg_pedido_str})"
    else:
        additional_condition_cfg_ped = ""

    query =  f"""
        SELECT 
            ITEMAGRO.ITEM, 
            ITEMAGRO.DESCRICAO, 
            SUM(PEDCAB.valormercadoria) AS Total_Compras 
        FROM 
            PEDCAB
        JOIN
            PEDCFG ON PEDCFG.PEDIDOCONF = PEDCAB.PEDIDOCONF 
        JOIN 
            PEDITEM ON PEDCAB.NUMERO = PEDITEM.NUMERO
        JOIN 
            ITEMAGRO ON PEDITEM.ITEM = ITEMAGRO.ITEM 
        JOIN 
            PREPRESE ON PREPRESE.REPRESENT = PEDCAB.REPRESENT
        JOIN 
            (SELECT DISTINCT TABPRC FROM ITEMTABPRC WHERE 1=1 {additional_condition_tab}) TABPRC_FILTRADO ON TABPRC_FILTRADO.TABPRC = PEDCAB.TABPRC          
        WHERE 
            PEDCAB.SERIE = 'PV' 
            AND PEDCAB.STATUS = 'B'
            AND PEDCAB.DTEMISSAO BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD') 
            AND TO_DATE('{end_date}', 'YYYY-MM-DD')
            {additional_condition}
            {additional_condition_emp}
            {additional_condition_cfg_ped}
        GROUP BY 
            ITEMAGRO.ITEM, ITEMAGRO.DESCRICAO
        ORDER BY
            TOTAL_COMPRAS DESC
            FETCH FIRST 10 ROWS ONLY
        """
    df = pd.read_sql(query, conn)
    
    # Ordenar o DataFrame do maior para o menor valor de 'TOTAL_COMPRAS'
    df = df.sort_values(by='TOTAL_COMPRAS', ascending=False)

    # Calcula o número total de registros
    num_registros = len(df)

    # Define a cor padrão para todos os registros
    cores = ['#17a2b8'] * num_registros

    produto = df['DESCRICAO'].tolist()
    total_compras = [f'R$ {locale.currency(valor, grouping=True, symbol=None)}' for valor in df['TOTAL_COMPRAS']]

    # Ajusta as cores dos três primeiros registros para verde
    if num_registros >= 3:
        cores[:3] = ['green'] * 3

    hover_text = [
        f"Descrição: {con}<br>Valor: {val}<br>"
        for con, val in zip(produto, total_compras)
    ]

    return {
        'data': [
            {
                'y': produto,
                'x': df['TOTAL_COMPRAS'],
                'type': 'bar',
                'orientation': 'h',
                'name': 'Total Compras',
                'hovertemplate': hover_text,
                'text': total_compras,  # Texto ao lado das barras
                'marker': {'color': cores},
            }
        ],
        'layout': {
            'title': {
                'text': 'Valor Líquido por Produto',
                'font': {'color': 'white'}
            },
            'plot_bgcolor': '#343a40',
            'paper_bgcolor': '#343a40',
            'font': {'color': 'white'},
            'xaxis': {
                'title': 'Total de Vendas',
                'gridcolor': '#495057',
            },
            'yaxis': {'title': 'Clientes', 
                      'tickfont': {'size': 10, 'color': 'white'}, 
                      'gridcolor': '#495057', 'autorange': "reversed"},
            'margin': {'l': 150, 'r': 50, 't': 50, 'b': 50},
            'dragmode': False,
            'scrollZoom': False,
        }
    }
