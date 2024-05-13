import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
import locale
from conexao_banco_dados import get_connection


# Definir a localização para pt_BR
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Estabelecer a conexão com o banco de dados Oracle
conn = get_connection()

def create_layout():
    layout = html.Div(id='container-pedidos-pendentes', children=[
        dbc.Row([
            dbc.Col(width=1),  # Coluna vazia para ocupar 1/3 do espaço à esquerda
            dbc.Col(
                dbc.Card([
                    html.Div(
                        [
                            html.H2("Pedidos Pendentes para Faturar", style={"font-family": "Voltaire", "font-size": "20px", "text-align": "center"}),
                        ],
                        style={"padding": "10px"}  # Adiciona um espaço interno ao div para centralizar o texto
                    ),
                    dbc.Row([
                        dbc.Col([
                            dcc.Graph(
                                id='bar-chart-top-clientes',
                                config={'displayModeBar': False}  # Desabilita a barra de ferramentas (incluindo o zoom pelo mouse)
                            )
                        ])
                    ])
                ]), width=4  # Coluna para ocupar 1/3 do espaço no centro
            ),
            dbc.Col(width=1),  # Coluna vazia para ocupar 1/3 do espaço à direita
        ])
    ])
    
    return layout

def update_chart(start_date, end_date, conn, selecter_rep_ids=None, selected_emp_ids=None, selected_tabpreco_id=None,selected_cfgpedido_id=None):

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


    if selecter_rep_ids:
        rep_ids_str = ", ".join(f"'{rep_id}'" for rep_id in selecter_rep_ids)
        additional_condition = f" AND PREPRESE.REPRESENT IN ({rep_ids_str})"
    else:
        additional_condition = ""
    
    if selected_cfgpedido_id:
        cfg_ped_str = ", ".join(f"'{cfg_id}'" for cfg_id in selected_cfgpedido_id)
        additional_condition_cfg_ped = f" AND PEDCFG.PEDIDOCONF IN ({cfg_ped_str})"
    else:
        additional_condition_cfg_ped = ""

    query = f"""
    SELECT
        CONTAMOV.NOME, 
        SUM(PEDCAB.valormercadoria) AS Total_Compras,
        MAX(PEDCAB.NUMERO) AS Numero_Pedido,
        MAX(PEDCAB.DTEMISSAO) AS Data_Emissao
    FROM 
        PEDCAB 
    JOIN 
        PREPRESE ON PREPRESE.REPRESENT = PEDCAB.REPRESENT
    JOIN
        PEDCFG ON PEDCFG.PEDIDOCONF = PEDCAB.PEDIDOCONF         
    JOIN
        CONTAMOV ON CONTAMOV.NUMEROCM = PEDCAB.PESSOA
    JOIN 
    	PEMPRESA ON PEDCAB.ESTAB = PEMPRESA.EMPRESA 
    JOIN 
        (SELECT DISTINCT TABPRC FROM ITEMTABPRC WHERE 1=1 {additional_condition_tab}) TABPRC_FILTRADO ON TABPRC_FILTRADO.TABPRC = PEDCAB.TABPRC
    WHERE
        PEDCAB.SERIE = 'PV'
    AND 
        pedcab.STATUS = 'N' 
    AND
        PEDCAB.DTEMISSAO BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD') AND TO_DATE('{end_date}', 'YYYY-MM-DD')
    {additional_condition}
    {additional_condition_emp}
    {additional_condition_cfg_ped}
    GROUP BY 
        CONTAMOV.NOME
    ORDER BY
        TOTAL_COMPRAS DESC
        FETCH FIRST 10 ROWS ONLY
    """
    # Executa a consulta SQL e lê os dados em um DataFrame
    df = pd.read_sql(query, conn)   


    # Ordenar o DataFrame do maior para o menor valor de 'TOTAL_COMPRAS'
    df = df.sort_values(by='TOTAL_COMPRAS', ascending=False)

    clientes = df['NOME'].tolist()
    total_compras = [f'R$ {locale.currency(valor, grouping=True, symbol=None)}' for valor in df['TOTAL_COMPRAS']]

    # Calcula o número total de registros
    num_registros = len(df)

    # Define a cor padrão para todos os registros
    cores = ['#17a2b8'] * num_registros

    # Ajusta as cores dos três primeiros registros para verde
    if num_registros >= 3:
        cores[:3] = ['green'] * 3

    hover_text = [f"Cliente: {cli}<br>Valor: {val}" 
                    for cli, val in zip(clientes, total_compras)]
    
    # Truncar nomes longos com elipses
    df['NOME'] = df['NOME'].apply(lambda x: (x[:12] + '...') if len(x) > 15 else x)

    clientes = df['NOME'].tolist()


    darkly_layout = {
        'plot_bgcolor': '#343a40',
        'paper_bgcolor': '#343a40',
        'font': {'color': 'white'},
        'title': 'Pedidos Pendentes para Faturar',
        'xaxis': {'title': 'Total de Compras', 'color': 'white', 'gridcolor': '#495057'},
        'yaxis': {'title': 'Clientes', 'tickfont': {'size': 10, 'color': 'white'}, 'gridcolor': '#495057', 'autorange': "reversed"},
        'dragmode': False,
        'scrollZoom': False,
        'margin': {'l': 150, 'r': 50, 't': 50, 'b': 50},
    }

    data = [
        {
            'y': clientes,
            'x': df['TOTAL_COMPRAS'].tolist(),
            'type': 'bar',
            'orientation': 'h',
            'name': 'Total Compras',
            'hovertemplate': hover_text,
            'text': total_compras,
            'hoverinfo': 'text',
            'marker': {'color': cores},
        }
    ]

    return {'data': data, 'layout': darkly_layout}
