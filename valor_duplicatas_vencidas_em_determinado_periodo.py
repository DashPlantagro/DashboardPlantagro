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

def valor_total_duplicatas_vencidas(start_date=None, end_date=None):
    # se não receber datas, define um intervalo padrão (exemplo: mês atual)
    if start_date is None or end_date is None:
        end_date = datetime.today().strftime('%Y-%m-%d')
        start_date = (datetime.today() - pd.DateOffset(months=1)).strftime('%Y-%m-%d')
    query = f""" 
SELECT
    SUM(PDUPREC.VALOR) AS TOTAL_VALOR
FROM
    PDUPREC
WHERE
    PDUPREC.DTVENCTO BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD')
    AND TO_DATE('{end_date}', 'YYYY-MM-DD')
    AND PDUPREC.QUITADA ='N'    """
    
    df = pd.read_sql(query, conn)
    
    total_duplicata = df['TOTAL_VALOR'].iloc[0] if not df.empty else 0

    if total_duplicata is None:
        total_duplicata = 0
    total_duplicata_formatado = locale.format_string('%.2f', total_duplicata, grouping=True)

    return total_duplicata_formatado

def create_layout():
    total_duplicatas = valor_total_duplicatas_vencidas()  # busca a soma de todas as vendas realizadas em X periodo
    layout = html.Div(id='container-valor-total-duplicatas-vencidas', children=[
        dbc.Row([
            dbc.Col(width=1),
            dbc.Col(
                dbc.Card([
                    html.H2('Total de Duplicatas a Receber Vencidas no Periodo', style={"font-family": "Voltaire", "font-size": "20px", "text-align": "center"}),
                    html.H3(f'Soma de Total de Duplicatas Vencidas: R$ {total_duplicatas}', style={"text-align": "center"})
                ],
                    style={"padding": "10px"}
                ),
                width=4
            ), dbc.Col(width=1)
        ])
    ])
    return layout
