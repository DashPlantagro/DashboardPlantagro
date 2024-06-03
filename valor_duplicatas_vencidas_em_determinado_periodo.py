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
            SUM(PDUPREC.VALOR) AS TOTAL_VALOR,
            SUM(PDUPREC.DESCONTO) AS VALOR_DESCONTO,
            SUM(PDUPREC.MULTA) AS MULTA, 
            SUM(PDUPREC.JUROS) AS JUROS,
            SUM(VWM_DUPLICATASRECEBER_EMPRESA.RECEBIDO) AS RECEBIDO,
            SUM(PDUPREC.VALOR) - SUM(PDUPREC.DESCONTO) + SUM(PDUPREC.JUROS) + SUM(PDUPREC.MULTA) - SUM(VWM_DUPLICATASRECEBER_EMPRESA.RECEBIDO) AS TOTAL_CALCULADO
        FROM
            PDUPREC
        LEFT JOIN 
            VWM_DUPLICATASRECEBER_EMPRESA ON VWM_DUPLICATASRECEBER_EMPRESA.DUPREC = PDUPREC.DUPREC AND VWM_DUPLICATASRECEBER_EMPRESA.EMPRESA = PDUPREC.EMPRESA 
        WHERE
            PDUPREC.DTVENCTO BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD')
            AND TO_DATE('{end_date}', 'YYYY-MM-DD')
            AND PDUPREC.QUITADA = 'N'
    """
    
    df = pd.read_sql(query, conn)
    
    if df.empty:
        return {
            'TOTAL_VALOR': 0,
            'VALOR_DESCONTO': 0,
            'MULTA': 0,
            'JUROS': 0,
            'RECEBIDO': 0,
            'TOTAL_CALCULADO': 0
        }
    
    return {
        'TOTAL_VALOR': df['TOTAL_VALOR'].iloc[0] or 0,
        'VALOR_DESCONTO': df['VALOR_DESCONTO'].iloc[0] or 0,
        'MULTA': df['MULTA'].iloc[0] or 0,
        'JUROS': df['JUROS'].iloc[0] or 0,
        'RECEBIDO': df['RECEBIDO'].iloc[0] or 0,
        'TOTAL_CALCULADO': df['TOTAL_CALCULADO'].iloc[0] or 0
    }
