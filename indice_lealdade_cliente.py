import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
import locale
from datetime import datetime
from conexao_banco_dados import get_connection

# Definir o local BR
locale.setlocale(locale.LC_ALL, 'pt-BR.UTF8')

# Conectar BD
conn = get_connection()

def clientes_ativos_periodo(start_date=None, end_date=None, selected_reps_ids=None,selected_emp_ids=None,selected_tabpreco_id=None, selected_cfgpedido_id=None):
    # Se não receber datas, define um intervalo padrão (exemplo: último mês)
    if start_date is None or end_date is None:
        end_date = datetime.today().strftime('%Y-%m-%d')
        start_date = (datetime.today() - pd.DateOffset(months=1)).strftime('%Y-%m-%d')


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

    if selected_cfgpedido_id:
        cfg_pedido_str = ", ".join(f"'{tab_id}'" for tab_id in selected_cfgpedido_id)
        additional_condition_cfg_ped = f" AND NFCAB.NOTACONF  IN ({cfg_pedido_str})"
    else:
        additional_condition_cfg_ped = ""

    # Tratamento da lista de representantes
    if selected_reps_ids:
        reps_ids_str = ", ".join(f"'{rep_id}'" for rep_id in selected_reps_ids)
        additional_condition = f" AND PREPRESE.REPRESENT IN ({reps_ids_str})"
    else:
        additional_condition = ""

    query = f"""
        SELECT
            COUNT(DISTINCT NFCAB.NUMEROCM) AS TOTAL_COMPRAS
        FROM 
            NFCAB
        JOIN
            PREPRESE ON NFCAB.REPRESENT = PREPRESE.REPRESENT
        JOIN
            NFCFG ON NFCFG.NOTACONF = NFCAB.NOTACONF
        JOIN 
            CONTAMOV ON CONTAMOV.NUMEROCM = NFCAB.NUMEROCM
        LEFT JOIN
            ITEMTABPRC ON ITEMTABPRC.ESTAB = NFCAB.ESTAB AND ITEMTABPRC.TABPRC = NFCAB.TABPRC
        WHERE
            NFCAB.DTEMISSAO BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD') AND TO_DATE('{end_date}', 'YYYY-MM-DD')
            AND 
                NFCAB.NOTACONF NOT IN (2, 6)
            AND 
                NFCAB.STATUS = 'N'
            AND 
                NFCFG.INATIVA = 'N'
            AND
                 NFCFG.ENTRADASAIDA = 'S'
            {additional_condition}
            {additional_condition_emp}
            {additional_condition_cfg_ped}
            {additional_condition_tab}
            """
    df = pd.read_sql(query, conn)
    return df['TOTAL_COMPRAS'].iloc[0] if not df.empty else 0 

def create_layout():
    total_clientes_ativos = clientes_ativos_periodo()  # Busca o total de clientes
    layout = html.Div(id='container-total-clientes-ativos-periodo', children=[
        dbc.Row([
            dbc.Col(width=1),
            dbc.Col(
                dbc.Card([
                    html.H2('Total de Clientes Ativos por Periodo', style={"font-family": "Voltaire", "font-size": "20px", "text-align": "center"}),
                    html.H3(f'Total de Clientes: {total_clientes_ativos}', style={"text-align": "center"})  # Exibe o total de clientes aqui
                ],
                    style={"padding":"10px"}
                ),
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(
                            id='bar-chart-total-clientes-ativos',
                            # A figura é definida em outro lugar, possivelmente através de um callback se necessário
                        )
                    ])
                ]), width=4
            ), dbc.Col(width=1),
        ])
    ])
    return layout
