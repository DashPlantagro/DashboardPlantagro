import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
import locale
from conexao_banco_dados import get_connection

# Definir a localização para pt_BR
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Estabelecer a conexão com o banco de dados Oracle
conn = get_connection()


def update_chart(start_date,end_date,selected_rep_ids, selected_emp_ids, selected_tabpreco_id, selected_cfgpedido_id):
    # Construção das cláusulas de filtro baseadas nas seleções do usuário
    tab_ids_clause = f"AND ITEMTABPRC.TABPRC IN ({', '.join(f"'{tab_id}'" for tab_id in selected_tabpreco_id)})" if selected_tabpreco_id else ""
    emp_ids_clause = f"AND NFCAB.ESTAB IN ({', '.join(f"'{emp_id}'" for emp_id in selected_emp_ids)})" if selected_emp_ids else ""
    rep_ids_clause = f"AND PREPRESE.REPRESENT IN ({', '.join(f"'{rep_id}'" for rep_id in selected_rep_ids)})" if selected_rep_ids else ""
    cfg_ids_clause = f"AND NFCAB.NOTACONF IN ({', '.join(f"'{cfg_ped}'" for cfg_ped in selected_cfgpedido_id)})" if selected_cfgpedido_id else ""

    # Montagem da consulta SQL com as cláusulas de filtro, incluindo a subconsulta para ITEMTABPRC
    query = f"""
    SELECT
        CONTAMOV.NUMEROCM AS Cliente,
        MAX(CONTAMOV.NOME) AS Nome,
        SUM(NFITEM.VALORTOTAL) AS Total_Compras
    FROM
        CONTAMOV
    JOIN
        NFCAB ON CONTAMOV.NUMEROCM = NFCAB.NUMEROCM
    JOIN
        PREPRESE ON NFCAB.REPRESENT = PREPRESE.REPRESENT
    JOIN
        NFCFG ON NFCFG.NOTACONF = NFCAB.NOTACONF
    LEFT JOIN
        ITEMTABPRC ON ITEMTABPRC.ESTAB = NFCAB.ESTAB AND ITEMTABPRC.TABPRC = NFCAB.TABPRC
	JOIN
        NFITEM ON NFITEM.SEQNOTA = NFCAB.SEQNOTA AND NFITEM.ESTAB = NFCAB.ESTAB
    WHERE
         NFCAB.DTEMISSAO BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD') AND TO_DATE('{end_date}', 'YYYY-MM-DD')
        {rep_ids_clause}
        {emp_ids_clause}
        {cfg_ids_clause}
        {tab_ids_clause}
        AND NFCFG.ENTRADASAIDA = 'S'
    GROUP BY CONTAMOV.NUMEROCM
    ORDER BY Total_Compras DESC
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
    
    clientes = df['NOME'].tolist()
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

    # Formatando o valor para o formato monetário brasileiro com o símbolo "R$"
    total_compras = [f'R$ {locale.currency(valor, grouping=True, symbol=None)}' for valor in df['TOTAL_COMPRAS']]
    hover_text = [
        f"Cliente: {cli} <br> Valor: {val}"
        for cli, val in zip(clientes, total_compras)
    ]

    # Truncar nomes longos com elipses
    df['NOME'] = df['NOME'].apply(lambda x: (x[:12] + '...') if len(x) > 15 else x)

    clientes = df['NOME'].tolist()


    # Dados do gráfico
    dados_grafico = [{
        'y': clientes,
        'x': df['TOTAL_COMPRAS'],  
        'type': 'bar',
        'orientation': 'h',
        'name': 'Total Vendido',
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
        'title': 'Top 10 Clientes que mais Compraram',
        'xaxis': {'title': 'Total de Compras', 'gridcolor': '#495057', 'color': 'white'},
        'yaxis': {'title': 'Clientes', 'tickfont': {'size': 10, 'color': 'white'}, 'gridcolor': '#495057','autorange': "reversed"},
        'dragmode': False,
        'scrollZoom': False,
        'margin': {'l': 150, 'r': 50, 't': 50, 'b': 50},
    }

    # Preparando o retorno para o Dash
    return {'data': dados_grafico, 'layout': fig_layout}