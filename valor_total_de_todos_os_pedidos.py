import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
import locale
from datetime import datetime
from conexao_banco_dados import get_connection

# Definindo local BR
locale.setlocale(locale.LC_ALL, 'pt-BR.UTF8')

# Conectar BD
conn = get_connection()

def sumarizacao_total_dos_pedidos(start_date=None, end_date=None, selected_reps_ids=None,selected_emp_ids=None, selected_tabpreco_id=None,selected_cfgpedido_id=None):

    if selected_tabpreco_id:
        tab_ids_str = ", ".join(f"'{tab_id}'" for tab_id in selected_tabpreco_id)
        additional_condition_tab = f" AND ITEMTABPRC.TABPRC IN ({tab_ids_str})"
    else:
        additional_condition_tab = ""

    # Se não receber datas, define um intervalo padrão (exemplo: último mês)
    if not start_date or not end_date:
        end_date = datetime.today().strftime('%Y-%m-%d')
        start_date = (datetime.today() - pd.DateOffset(months=1)).strftime('%Y-%m-%d')

    # Tratamento dos representantes selecionados
    reps_filter = ""
    if selected_reps_ids:
        rep_ids_str = ", ".join(f"'{rep_id}'" for rep_id in selected_reps_ids)
        reps_filter = f" AND NFCAB.REPRESENT IN ({rep_ids_str})"

    if selected_cfgpedido_id:
        cfg_pedido_str = ", ".join(f"'{tab_id}'" for tab_id in selected_cfgpedido_id)
        additional_condition_cfg_ped = f" AND NFCAB.NOTACONF  IN ({cfg_pedido_str})"
    else:
        additional_condition_cfg_ped = ""

    if selected_emp_ids:
        emp_ids_str = ", ".join(f"'{emp_id}'" for emp_id in selected_emp_ids)
        additional_condition_emp = f" AND NFCAB.ESTAB IN ({emp_ids_str})"
    else:
        additional_condition_emp = ""

    # Construção da query com tratamento para retornar 0 caso não haja vendas
    query = f""" 
        SELECT
            COALESCE(SUM(NFITEM.VALORTOTAL), 0) AS TOTAL_VENDAS_LIQUIDO
        FROM
            NFCAB
        LEFT JOIN
            PREPRESE ON PREPRESE.REPRESENT = NFCAB.REPRESENT
        JOIN
            NFCFG ON NFCFG.NOTACONF = NFCAB.NOTACONF
        LEFT JOIN
            ITEMTABPRC ON ITEMTABPRC.ESTAB = NFCAB.ESTAB AND ITEMTABPRC.TABPRC = NFCAB.TABPRC
        LEFT JOIN
            NFITEM ON NFITEM.SEQNOTA = NFCAB.SEQNOTA AND NFITEM.ESTAB = NFCAB.ESTAB
        WHERE
                NFCAB.DTEMISSAO BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD')
                AND TO_DATE('{end_date}', 'YYYY-MM-DD')
            AND NFCFG.ENTRADASAIDA IN 'S'
                {reps_filter}
                {additional_condition_cfg_ped}
                {additional_condition_emp}
                {additional_condition_tab}
            
    """
    # Execução da consulta e tratamento de erro
    try:
        df = pd.read_sql(query, conn)
        total_vendas_liquido = df['TOTAL_VENDAS_LIQUIDO'].iloc[0]
    except Exception as e:
        print(f"Erro ao executar a consulta: {e}")
        total_vendas_liquido = 0

    # Formatação do valor total para o formato de moeda
    total_vendas_formatado = locale.format_string('%.2f', total_vendas_liquido, grouping=True)

    return total_vendas_formatado

def create_layout():
    total_vendas = sumarizacao_total_dos_pedidos()  # busca a soma de todas as vendas realizadas em X periodo
    layout = html.Div(id='container-valor-total-de-todos-pedidos', children=[
        dbc.Row([
            dbc.Col(width=1),
            dbc.Col(
                dbc.Card([
                    html.H2('Soma do Total de Todos os Pedidos em Determinado Periodo', style={"font-family": "Voltaire", "font-size": "20px", "text-align": "center"}),
                    # Aqui você exibe o valor já formatado
                    html.H3(f'Soma de Todas as Vendas: R$ {total_vendas}', style={"text-align": "center"})
                ],
                    style={"padding": "10px"}
                ),
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(
                            id='bar-chart-total-vendas-por-periodo'
                        )
                    ])
                ]), width=4
            ), dbc.Col(width=1)
        ])
    ])
    return layout