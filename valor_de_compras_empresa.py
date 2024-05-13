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

def valor_total_das_compras(start_date,end_date,selected_rep_ids, selected_emp_ids, selected_tabpreco_id, selected_cfgpedido_id):
    # se não receber datas, define um intervalo padrão (exemplo: mes atual)
    if start_date is None or end_date is None:
        end_date = datetime.today().strftime('%Y-%m-%d')
        start_date = (datetime.today() - pd.DateOffset(months=1)).strftime('%Y-%m-%d')
    # Construção das cláusulas de filtro baseadas nas seleções do usuário
    tab_ids_clause = f"AND ITEMTABPRC.TABPRC IN ({', '.join(f"'{tab_id}'" for tab_id in selected_tabpreco_id)})" if selected_tabpreco_id else ""
    emp_ids_clause = f"AND NFCAB.ESTAB IN ({', '.join(f"'{emp_id}'" for emp_id in selected_emp_ids)})" if selected_emp_ids else ""
    rep_ids_clause = f"AND PREPRESE.REPRESENT IN ({', '.join(f"'{rep_id}'" for rep_id in selected_rep_ids)})" if selected_rep_ids else ""
    cfg_ids_clause = f"AND NFCAB.NOTACONF IN ({', '.join(f"'{cfg_ped}'" for cfg_ped in selected_cfgpedido_id)})" if selected_cfgpedido_id else ""
    
    query = f""" 
            SELECT 
                COALESCE(SUM(NFITEM.VALORTOTAL), 0) AS Total_Compras
            FROM
                NFCAB
            JOIN
                NFCFG ON NFCFG.NOTACONF = NFCAB.NOTACONF 
            JOIN
                CONTAMOV ON CONTAMOV.NUMEROCM = NFCAB.NUMEROCM 
            LEFT JOIN
                PREPRESE ON PREPRESE.REPRESENT = NFCAB.REPRESENT
            LEFT JOIN
                ITEMTABPRC ON ITEMTABPRC.ESTAB = NFCAB.ESTAB AND ITEMTABPRC.TABPRC = NFCAB.TABPRC
            LEFT JOIN
                NFITEM ON NFITEM.SEQNOTA = NFCAB.SEQNOTA AND NFITEM.ESTAB = NFCAB.ESTAB
            WHERE
                NFCAB.DTEMISSAO BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD')
            AND
                TO_DATE('{end_date}', 'YYYY-MM-DD')
            AND 
                NFCFG.ENTRADASAIDA = 'E'
                {rep_ids_clause}
                {emp_ids_clause}
                {cfg_ids_clause}
                {tab_ids_clause}
            """
    df = pd.read_sql(query, conn)
    total_vendas_liquido = df['TOTAL_COMPRAS'].iloc[0] if not df.empty else 0

    # Formatação do valor total para o formato de moeda
    total_vendas_formatado = locale.format_string('%.2f', total_vendas_liquido, grouping=True)
    return total_vendas_formatado

def create_layout():
    total_compras = valor_total_das_compras()  # busca a soma de todas as vendas realizadas em X periodo
    layout = html.Div(id='container-valor-total-de-compras', children=[
        dbc.Row([
            dbc.Col(width=1),
            dbc.Col(
                dbc.Card([
                    html.H2('Soma do Total de Todas as Compras em Determinado Periodo', style={"font-family": "Voltaire", "font-size": "20px", "text-align": "center"}),
                    # Aqui você exibe o valor já formatado
                    html.H3(f'Soma de Todas as Compras: R$ {total_compras}', style={"text-align": "center"})
                ],
                    style={"padding": "10px"}
                ),
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(
                            id='bar-chart-total-compras-por-periodo'
                        )
                    ])
                ]), width=4
            ), dbc.Col(width=1)
        ])
    ])
    return layout