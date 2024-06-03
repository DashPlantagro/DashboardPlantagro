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

def valor_total_contas_a_pagar_vencidas(start_date=None, end_date=None):
    # se não receber datas, define um intervalo padrão (exemplo: mês atual)
    if start_date is None or end_date is None:
        end_date = datetime.today().strftime('%Y-%m-%d')
        start_date = (datetime.today() - pd.DateOffset(months=1)).strftime('%Y-%m-%d')

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
    """
    
    df = pd.read_sql(query, conn)
    print('SQL VALOR DUPLICATAS A PAGAR: ' + query)
    
    total_duplicata_pagar = df['TOTAL_VALOR'].iloc[0] if not df.empty else 0

    if total_duplicata_pagar is None:
        total_duplicata_pagar = 0
    total_duplicata_pagar_formatado = locale.format_string('%.2f', total_duplicata_pagar, grouping=True)

    return total_duplicata_pagar_formatado
