import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
import locale
from conexao_banco_dados import get_connection
from datetime import datetime

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

# Estabelecer a conexão com o banco de dados Oracle
conn = get_connection()

def update_chart(start_date, end_date, selected_rep_ids,selected_emp_ids, selected_tabpreco_id,selected_cfgpedido_id):

    # Define o período padrão desde o primeiro dia do ano até a data atual, caso não seja fornecido
    if start_date is None or end_date is None:
        hoje = datetime.now()
        primeiro_dia_do_ano = datetime(hoje.year, 1, 1).strftime('%Y-%m-%d')
        data_atual = hoje.strftime('%Y-%m-%d')
    else:
        primeiro_dia_do_ano = datetime.strptime(start_date, '%Y-%m-%d').strftime('%Y-%m-%d')
        data_atual = datetime.strptime(end_date, '%Y-%m-%d').strftime('%Y-%m-%d')



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

    # Executa a consulta SQL
    query = f"""
        SELECT
            pempresa.FANTASIA,
            pempresa.EMPRESA,
            TRUNC(MAX(NFCAB.DTEMISSAO)) AS data_pedido,
            SUM(NFITEM.VALORTOTAL) AS total_vendas
        FROM
            NFCAB
        JOIN
            pempresa ON NFCAB.ESTAB = pempresa.EMPRESA
        LEFT JOIN
            PREPRESE ON PREPRESE.REPRESENT = NFCAB.REPRESENT
        LEFT JOIN
            ITEMTABPRC ON ITEMTABPRC.ESTAB = NFCAB.ESTAB AND ITEMTABPRC.TABPRC = NFCAB.TABPRC
        LEFT JOIN
            NFITEM ON NFITEM.SEQNOTA = NFCAB.SEQNOTA AND NFITEM.ESTAB = NFCAB.ESTAB
        JOIN
            NFCFG ON NFCFG.NOTACONF = NFCAB.NOTACONF
        WHERE
            NFCAB.DTEMISSAO BETWEEN TO_DATE(:primeiro_dia_do_ano, 'YYYY-MM-DD') AND TO_DATE(:data_atual, 'YYYY-MM-DD')
            {additional_condition_emp}
            {additional_condition}
            {additional_condition_cfg_ped}
            {additional_condition_tab}
            AND NFCFG.ENTRADASAIDA IN 'S'
        GROUP BY 
            pempresa.FANTASIA,
            pempresa.EMPRESA
        ORDER BY 
            TO_NUMBER(pempresa.EMPRESA)
    """

    # Aqui você executa a consulta. Certifique-se de que 'conn' seja uma conexão válida ao banco de dados
    df = pd.read_sql(query, conn, params={'primeiro_dia_do_ano': primeiro_dia_do_ano, 'data_atual': data_atual})
    df['EMPRESA'] = df['EMPRESA'].astype(str)
    # Formata a coluna 'TOTAL_VENDAS' para o padrão monetário brasileiro
    df['TOTAL_VENDAS_formatado'] = df['TOTAL_VENDAS'].apply(formatar_para_moeda_brasileira)

    data = [{
        'x': df['FANTASIA'],
        'y': df['TOTAL_VENDAS'],
        'type': 'bar',
        'text': df['TOTAL_VENDAS_formatado'],
        'hoverinfo': 'text+x',
        'marker': {'color': '#17BECF'}
    }]

    layout = {
        'title': {
            'text': 'Total de Vendas Anuais por Estabelecimento (primeiro dia do ano até a data atual)',
            'font': {'color': 'white'}
        },
        'xaxis': {
            'title': 'Estabelecimento',
            'title_font': {'color': 'white'},
            'tickfont': {'color': 'white'}
        },
        'yaxis': {
            'title': 'Total de Vendas',
            'title_font': {'color': 'white'},
            'tickfont': {'color': 'white'}
        },
        'paper_bgcolor': '#222',
        'plot_bgcolor': '#222',
        'margin': {'l': 50, 'r': 50, 't': 50, 'b': 150},
        'dragmode': False,
        'scrollZoom': False,
        'xaxis_tickangle': -45
    }

    # Retornando um componente dcc.Graph com a figura e um ID específico
    return dcc.Graph(
        id='container-grafico-vendas-anuais',
        figure={
            'data': data,
            'layout': layout
        }
    )