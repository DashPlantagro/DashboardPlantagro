import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
import locale
from conexao_banco_dados import get_connection

# Defindo localização PTBR
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF8')

# Conectar BD
conn = get_connection()

def create_layout():
    layout = html.Div(id='container-valor-liquido-vendedor', children=[
        dbc.Row([
            dbc.Col(width=1),  # Coluna vazia para ocupar espaço à esquerda
            dbc.Col(
                dbc.Card([
                    html.Div([
                        html.H2('Valor Líquido por Vendedor', style={"font-family": "Voltaire", "font-size": "20px", "text-align": "center", "color": "white"}),
                    ],
                    style={"padding": "10px", "backgroundColor": "#343a40"}  # Ajuste para tema DARKLY
                    ),
                    dbc.Row([
                        dbc.Col([
                            dcc.Graph(
                                id='bar-chart-valor-liquido-vendedor',
                                config={'displayModebar': False}
                            )
                        ])
                    ])
                ], style={"backgroundColor": "#343a40", "border": "1px solid #495057"}),  # Ajuste para tema DARKLY
                width=10  # Ajuste para utilizar mais espaço
            ),
            dbc.Col(width=1),  # Coluna vazia para ocupar espaço à direita
        ], style={"padding": "20px"})  # Espaço externo para alinhamento
    ], style={"backgroundColor": "#343a40"})  # Fundo escuro para o contêiner
    
    return layout

def update_chart(start_date, end_date, selected_rep_ids,selected_emp_ids, selected_tabpreco_id,selected_cfgpedido_id):

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

    # Inicializa a condição adicional para o filtro de tabela de preço

    # Verifica se há algum ID de tabela de preço selecionado e prepara a condição
    if selected_tabpreco_id:
        tab_ids_str = ", ".join(f"'{tab_id}'" for tab_id in selected_tabpreco_id)
        additional_condition_tab = f" AND ITEMTABPRC.TABPRC IN ({tab_ids_str})"
    else:
        additional_condition_tab = ""

    if selected_cfgpedido_id:
        cfg_pedido_str = ", ".join(f"'{tab_id}'" for tab_id in selected_cfgpedido_id)
        additional_condition_cfg_ped = f" AND NFCFG.NOTACONF IN ({cfg_pedido_str})"
    else:
        additional_condition_cfg_ped = ""

    # Prepara a sua consulta SQL incorporando a condição dinâmica
    query = f"""
    SELECT
        PREPRESE.DESCRICAO,
        SUM(NFITEM.VALORTOTAL) AS Total_Compras
    FROM
        NFCAB
    JOIN
        NFCFG ON NFCFG.NOTACONF = NFCAB.NOTACONF
    LEFT JOIN
        PREPRESE ON PREPRESE.REPRESENT = NFCAB.REPRESENT
    LEFT JOIN
        ITEMTABPRC ON ITEMTABPRC.ESTAB = NFCAB.ESTAB AND ITEMTABPRC.TABPRC = NFCAB.TABPRC
    LEFT JOIN
        NFITEM ON NFITEM.SEQNOTA = NFCAB.SEQNOTA AND NFITEM.ESTAB = NFCAB.ESTAB
    WHERE
		NFCAB.DTEMISSAO BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD') 
        AND TO_DATE('{end_date}', 'YYYY-MM-DD')
        {additional_condition_emp}
        {additional_condition}
        {additional_condition_cfg_ped}
        {additional_condition_tab}
        AND NFCFG.ENTRADASAIDA IN 'S'
    GROUP BY 
        PREPRESE.DESCRICAO
    ORDER BY
        Total_Compras DESC
    FETCH FIRST 10 ROWS ONLY
    """  
    df = pd.read_sql(query, conn)
    
    

    # Assegura que o DataFrame está ordenado do maior para o menor valor de TOTAL_COMPRAS
    df = df.sort_values(by='TOTAL_COMPRAS', ascending=False)

    num_registros = len(df)  # Número total de registros no DataFrame

    # Inicialmente, todos os registros terão a cor padrão (azul)
    cores = ['#17a2b8'] * num_registros

    # Ajustar as cores dos três primeiros para verde, se houver pelo menos 3 registros
    if num_registros >= 3:
        for i in range(3):
            cores[i] = 'green'

    # Assegure-se de que não há valores None na coluna 'DESCRICAO'
    df['DESCRICAO'] = df['DESCRICAO'].fillna('Descrição Indisponível')

    # Após garantir que não há valores None, aplique a truncagem
    df['DESCRICAO'] = df['DESCRICAO'].apply(lambda x: (x[:12] + '...') if len(x) > 15 else x)



    # Prepara os dados para o gráfico
    descricao = df['DESCRICAO'].tolist()
    total_compras = [f'R$ {locale.currency(valor, grouping=True, symbol=None)}' for valor in df['TOTAL_COMPRAS']]
    hover_text = [f"Descrição: {con}<br>Valor: {val}" 
                  for con, val in zip(descricao, total_compras)
                  ]
    



    # Preparação dos dados e layout para o gráfico
    data = [{
        'y': descricao,
        'x': df['TOTAL_COMPRAS'].tolist(),  # Corrige a passagem dos dados
        'type': 'bar',
        'orientation': 'h',
        'name': 'Total Compras',
        'hovertemplate': hover_text,
        'text': total_compras,  # Caso queira exibir o texto sobre as barras
        'hoverinfo': 'text',
        'marker': {'color': cores},
    }]

    fig_layout = {
        'title': 'Valor Líquido por Vendedor',
        'plot_bgcolor': '#343a40',
        'paper_bgcolor': '#343a40',
        'font': {'color': 'white'},
        'xaxis': {'title': 'Total de Compras', 'gridcolor': '#495057'},
        'yaxis': {
            'title': 'Vendedor',
            'tickfont': {'size': 10, 'color': 'white'},
            'gridcolor': '#495057',
            'autorange': 'reversed'  # Garante que o maior valor fique no topo
        },
        'margin': {'l': 150, 'r': 50, 't': 50, 'b': 50},
        'dragmode': False,
        'scrollZoom': False,
    }

    # Retorna o gráfico configurado
    return {'data': data, 'layout': fig_layout}
