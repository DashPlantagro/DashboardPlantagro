import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
import locale
from datetime import datetime
from conexao_banco_dados import get_connection
import plotly.graph_objs as go

# Definindo local PTBR
locale.setlocale(locale.LC_ALL, 'pt-BR.UTF8')

# Conectar BD
conn = get_connection()


def create_gauge_chart_with_pointer(total_metas, total_pedidos):
    total_metas_formatado = locale.currency(total_metas, grouping=True)
    total_pedidos_formatado = locale.currency(total_pedidos, grouping=True)
    
    if total_metas > 0:
        porcentagem_atingida = (total_pedidos / total_metas) * 100
    else:
        porcentagem_atingida = 0

    fig = go.Figure()

    # Adiciona o gráfico de velocímetro
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=porcentagem_atingida,
        number={'suffix': "%"},
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Meta vs Pedidos"},
        gauge={'axis': {'range': [None, 100]},
               'bar': {'color': "blue"},
               'steps': [
                   {'range': [0, 10], 'color': "red"},
                   {'range': [10, 90], 'color': "yellow"},
                   {'range': [90, 100], 'color': "green"},
                ],
               }))

    # Ajusta o layout para reduzir a margem inferior
    fig.update_layout(margin=dict(t=15, l=15, r=15, b=15))

    # Adiciona anotações
    fig.add_annotation(x=0.5, y=0.1, text=f"Total da Meta: {total_metas_formatado}",
                       showarrow=False, font={'size': 14})
    fig.add_annotation(x=0.5, y=0.15, text=f"Valor Alcançado: {total_pedidos_formatado}",
                       showarrow=False, font={'size': 14})

    return fig



def total_metas(start_date=None, end_date=None, selected_reps_ids=None,selected_emp_ids=None,selected_tabpreco_id=None,selected_cfgpedido_id=None):
    # Define um intervalo padrão se não receber datas
    if start_date is None or end_date is None:
        end_date = datetime.today().strftime('%Y-%m-%d')
        start_date = (datetime.today() - pd.DateOffset(months=1)).strftime('%Y-%m-%d')

    # Cfg do pedido
    if selected_cfgpedido_id:
        cfg_pedido_str = ", ".join(f"'{tab_id}'" for tab_id in selected_cfgpedido_id)
        additional_condition_cfg_ped = f" AND PEDCFG.PEDIDOCONF IN ({cfg_pedido_str})"
    else:
        additional_condition_cfg_ped = ""

    # Trata a listagem dos representantes
    if selected_reps_ids:
        rep_ids_str = ", ".join(f"'{rep_id}'" for rep_id in selected_reps_ids)
        additional_conditional = f" AND PREPRESE.REPRESENT IN ({rep_ids_str})"
    else:
        additional_conditional = ""

    # tabela de preço
    if selected_tabpreco_id:
        tab_ids_str = ", ".join(f"'{tab_id}'" for tab_id in selected_tabpreco_id)
        additional_condition_tab = f" AND ITEMTABPRC.TABPRC IN ({tab_ids_str})"
    else:
        additional_condition_tab = ""

    # selecionar empresa    
    if selected_emp_ids:
        emp_ids_str = ", ".join(f"'{emp_id}'" for emp_id in selected_emp_ids)
        additional_condition_emp = f" AND PEDCAB.ESTAB IN ({emp_ids_str})"
    else:
        additional_condition_emp = ""


    # Ajusta a query para usar as variáveis dinamicamente
    query = f""" 
            SELECT
                (
                    SELECT SUM(U_BI_METADEVENDAS.VALOR)
                    FROM U_BI_METADEVENDAS
                    JOIN PREPRESE ON U_BI_METADEVENDAS.REPRESENT = PREPRESE.REPRESENT
                    WHERE U_BI_METADEVENDAS.DATAMETA >= TRUNC(SYSDATE, 'YY')
                    {additional_conditional}
                ) AS TOTAL_METAS_ANUAL,
                (
                    SELECT SUM(PEDCAB.VALORMERCADORIA)
                    FROM PEDCAB
                    JOIN PEDCFG ON PEDCFG.PEDIDOCONF = PEDCAB.PEDIDOCONF 
                    JOIN 
                    (
                        SELECT DISTINCT TABPRC 
                        FROM ITEMTABPRC 
                        WHERE 1=1 {additional_condition_tab}
                    ) TABPRC_FILTRADO ON TABPRC_FILTRADO.TABPRC = PEDCAB.TABPRC
                    JOIN PREPRESE ON PEDCAB.REPRESENT = PREPRESE.REPRESENT
                    WHERE PEDCAB.SERIE = 'PV'
                    {additional_condition_cfg_ped}
                    AND PEDCAB.STATUS = 'B'
                    {additional_condition_emp}
                    AND PEDCAB.DTEMISSAO BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD') AND TO_DATE('{end_date}', 'YYYY-MM-DD')
                    {additional_conditional}
                ) AS TOTAL_PEDIDOS_PERIODO
            FROM DUAL

        """
    # Executa a consulta
    df = pd.read_sql(query, conn)

    # Verifica se o DataFrame não está vazio e extrai os valores
    if not df.empty:
        total_metas = df.iloc[0]['TOTAL_METAS_ANUAL'] if df.iloc[0]['TOTAL_METAS_ANUAL'] is not None else 0
        total_pedidos = df.iloc[0]['TOTAL_PEDIDOS_PERIODO'] if df.iloc[0]['TOTAL_PEDIDOS_PERIODO'] is not None else 0
    else:
        total_metas = 0
        total_pedidos = 0

    return total_metas, total_pedidos
