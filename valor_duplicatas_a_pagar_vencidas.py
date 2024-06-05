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
            SUM(VWM_DUPLICATASPAGAR_EMPRESA.VALOR)  TOTAL_VALOR,
            SUM(VWM_DUPLICATASPAGAR_EMPRESA.JUROSPEND)   JUROS,
            SUM(VWM_DUPLICATASPAGAR_EMPRESA.DESCONTOS) DESCONTO,
            SUM(VWM_DUPLICATASPAGAR_EMPRESA.PAGO) PAGO,
            SUM(VWM_DUPLICATASPAGAR_EMPRESA.VALOR) + SUM(VWM_DUPLICATASPAGAR_EMPRESA.JUROSPEND) SALDO
        FROM
            VWM_DUPLICATASPAGAR_EMPRESA
        JOIN
    	    PEMPRESA ON PEMPRESA.EMPRESA = VWM_DUPLICATASPAGAR_EMPRESA.EMPRESA 
        WHERE
        VWM_DUPLICATASPAGAR_EMPRESA.DTVENCTO  BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD')
        AND TO_DATE('{end_date}', 'YYYY-MM-DD')
        AND VWM_DUPLICATASPAGAR_EMPRESA.QUITADA ='N'
    """
    
    df = pd.read_sql(query, conn)
    print('SQL VALOR DUPLICATAS A PAGAR: ' + query)

    if df.empty:
        return {
            'TOTAL_VALOR': 0,
            'DESCONTO': 0,
            'JUROS': 0,
            'PAGO': 0,
            'SALDO': 0
        }
    
    return {
        'TOTAL_VALOR': df['TOTAL_VALOR'].iloc[0] or 0,
        'DESCONTO': df['DESCONTO'].iloc[0] or 0,
        'JUROS': df['JUROS'].iloc[0] or 0,
        'PAGO': df['PAGO'].iloc[0] or 0,
        'SALDO': df['SALDO'].iloc[0] or 0
    }

