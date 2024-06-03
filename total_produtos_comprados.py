import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
import locale
from datetime import datetime
from conexao_banco_dados import get_connection

# Definir a localização para pt_BR
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Estabelecer a conexão com o banco de dados Oracle
conn = get_connection()

def create_layout():
    layout = html.Div(id='container-grafico-total-produtos-comprados', children=[
        dbc.Row([
            dbc.Col(width=1),  # Coluna vazia para ocupar 1/3 do espaço à esquerda
            dbc.Col(
                dbc.Card([
                    html.Div(
                        [
                            html.H2("Total por Produto Comprado", style={"font-family": "Voltaire", "font-size": "20px", "text-align": "center"}),
                        ],
                        style={"padding": "10px"}  # Adiciona um espaço interno ao div para centralizar o texto
                    ),
                    dbc.Row([
                        dbc.Col([
                            dcc.Graph(
                                id='bar-chart-total-produto-comprado',
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

def update_chart(start_date,end_date,selected_rep_ids, selected_emp_ids, selected_tabpreco_id, selected_cfgpedido_id):
    # se não receber datas, define um intervalo padrão (exemplo: mes atual)
    if start_date is None or end_date is None:
        end_date = datetime.today().strftime('%Y-%m-%d')
        start_date = (datetime.today() - pd.DateOffset(months=1)).strftime('%Y-%m-%d')
    # Construção das cláusulas de filtro baseadas nas seleções do usuário
    tab_ids_clause = f"AND ITEMTABPRC.TABPRC IN ({', '.join(f"'{tab_id}'" for tab_id in selected_tabpreco_id)})" if selected_tabpreco_id else ""
    emp_ids_clause = f"AND NFCAB.ESTAB IN ({', '.join(f"'{emp_id}'" for emp_id in selected_emp_ids)})" if selected_emp_ids else ""
    cfg_ids_clause = f"AND NFCAB.NOTACONF IN ({', '.join(f"'{cfg_ped}'" for cfg_ped in selected_cfgpedido_id)})" if selected_cfgpedido_id else ""
    rep_ids_clause = f"AND PREPRESE.REPRESENT IN ({', '.join(f"'{rep_id}'" for rep_id in selected_rep_ids)})" if selected_rep_ids else ""
    
    
    query = f"""
        SELECT
            ITEMAGRO.DESCRICAO AS PRODUTO,
            COALESCE(SUM(NFITEM.VALORTOTAL), 0) AS Total_Compras
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
            AND NFCFG.ENTRADASAIDA = 'E'
        {emp_ids_clause}
        {cfg_ids_clause}
        {tab_ids_clause}            
        {rep_ids_clause}   
        GROUP BY
            ITEMAGRO.DESCRICAO
        ORDER BY
            Total_Compras DESC
        FETCH FIRST 10 ROWS ONLY
                
    """
    # Executa a consulta SQL
    df = pd.read_sql(query, conn)
    

    if df.empty:
        return {
            'data': [],
            'layout': {
                'title': 'Nenhum dado disponível para os filtros selecionados.'
            }
        }
    
    # Ordenar o DataFrame do maior para o menor valor de 'TOTAL_COMPRAS'
    df = df.sort_values(by='TOTAL_COMPRAS', ascending=False)

    # Calcula o número total de registros
    num_registros = len(df)

    # Define a cor padrão para todos os registros
    cores = ['#17a2b8'] * num_registros
    total_compras = [f'R$ {locale.currency(valor, grouping=True, symbol=None)}' for valor in df['TOTAL_COMPRAS']]

    # Ajusta as cores dos três primeiros registros para verde
    if num_registros >= 3:
        cores[:3] = ['green'] * 3


    # Assegure-se de que não há valores None na coluna 'MARCA_PRODUTO'
    df['PRODUTO'] = df['PRODUTO'].fillna('Descrição Indisponível')

    # Aplicando truncagem
    df['PRODUTO'] = df['PRODUTO'].apply(lambda x: (x[:12] + '...') if len(x) > 15 else x)

    produto = df['PRODUTO'].tolist()

    # Formatando o valor para o formato monetário brasileiro com o símbolo "R$"
    total_compras = [f'R$ {locale.currency(valor, grouping=True, symbol=None)}' for valor in df['TOTAL_COMPRAS']]
    hover_text = [
        f"Marca: {cli} <br> Valor: {val}"
        for cli, val in zip(produto, total_compras)
    ]


    # Dados do gráfico
    dados_grafico = [{
        'y': produto,
        'x': df['TOTAL_COMPRAS'],  
        'type': 'bar',
        'orientation': 'h',
        'name': 'Total Comprado',
        'hovertemplate':hover_text,
        'text': total_compras,
        'hoverinfo': 'text',
        'marker': {'color': cores},  # Aqui usamos a lista de cores
    }]

    # Layout do gráfico
    fig_layout = {
        'plot_bgcolor': '#343a40',
        'paper_bgcolor': '#343a40',
        'font': {'color': 'white'},
        'title': 'Total Comprado por Produto',
        'xaxis': {'title': 'Total de Compras', 'gridcolor': '#495057', 'color': 'white'},
        'yaxis': {'title': 'Produto', 'tickfont': {'size': 10, 'color': 'white'}, 'gridcolor': '#495057','autorange': "reversed"},
        'dragmode': False,
        'scrollZoom': False,
        'margin': {'l': 150, 'r': 50, 't': 50, 'b': 50},
    }

    # Preparando o retorno para o Dash
    return {'data': dados_grafico, 'layout': fig_layout}