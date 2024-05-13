import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
import locale
from datetime import datetime
from conexao_banco_dados import get_connection

# Local BR
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF8')  # Certifique-se de que este é o locale correto para seu ambiente

# conectar BD
conn = get_connection()

def valor_total_contas_a_pagar_vencidas(start_date=None, end_date=None, selected_reps_ids=None):
    # se não receber datas, define um intervalo padrão (exemplo: mês atual)
    if start_date is None or end_date is None:
        end_date = datetime.today().strftime('%Y-%m-%d')
        start_date = (datetime.today() - pd.DateOffset(months=1)).strftime('%Y-%m-%d')

    # tratamento da listagem dos representantes
    if selected_reps_ids:
        rep_ids_str = ", ".join(f"'{rep_id}'" for rep_id in selected_reps_ids)
        additional_conditional = f" AND PREPRESE.REPRESENT IN ({rep_ids_str})"
    else:
        additional_conditional = ""

    query = f""" 
SELECT
    SUM(PDUPPAGA.VALOR) AS TOTAL_VALOR
FROM
    PDUPPAGA
JOIN
    PREPRESE ON PREPRESE.REPRESENT = PDUPPAGA.REPRESENT
WHERE
    PDUPPAGA.DTVENCTO BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD')
    AND TO_DATE('{end_date}', 'YYYY-MM-DD')
    AND PDUPPAGA.QUITADA ='N'
    {additional_conditional}
    """
    
    df = pd.read_sql(query, conn)
    
    total_duplicata_pagar = df['TOTAL_VALOR'].iloc[0] if not df.empty else 0

    if total_duplicata_pagar is None:
        total_duplicata_pagar = 0
    total_duplicata_pagar_formatado = locale.format_string('%.2f', total_duplicata_pagar, grouping=True)

    return total_duplicata_pagar_formatado

def create_layout():
    total_duplicatas_pagar_vencida = valor_total_contas_a_pagar_vencidas()  # busca a soma de todas as vendas realizadas em X periodo
    layout = html.Div(id='container-valor-total-duplicatas-a-pagar-vencidas', children=[
        dbc.Row([
            dbc.Col(width=1),
            dbc.Col(
                dbc.Card([
                    html.H2('Total de Duplicatas a Pagar Vencidas', style={"font-family": "Voltaire", "font-size": "20px", "text-align": "center"}),
                    html.H3(f'Soma de Total de Duplicatas Vencidas a Pagar Vencidas: R$ {total_duplicatas_pagar_vencida}', style={"text-align": "center"})
                ],
                    style={"padding": "10px"}
                ),
                width=4
            ), dbc.Col(width=1)
        ])
    ])
    return layout
