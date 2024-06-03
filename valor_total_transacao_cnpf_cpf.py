import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
import locale
from conexao_banco_dados import get_connection
from datetime import datetime

# Definir o local BR
locale.setlocale(locale.LC_ALL, 'pt-BR.UTF8')

# Conectar BD
conn = get_connection()

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


def update_chart(start_date=None, end_date=None, selected_reps_ids=None,selected_cfgpedido_id=None,selected_tabpreco_id=None,selected_emp_ids=None):
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
                CASE
                    WHEN LENGTH(CONTAMOV.CNPJF) = 11 THEN 'CPF'
                    WHEN LENGTH(CONTAMOV.CNPJF) = 14 THEN 'CNPJ'
                    ELSE 'Outro'
                END AS TipoDocumento,
                SUM(NFITEM.VALORTOTAL) AS TOTAL_VENDAS
            FROM
                NFCAB
            INNER JOIN
                CONTAMOV ON NFCAB.NUMEROCM  = CONTAMOV.NUMEROCM
            LEFT JOIN
                ITEMTABPRC ON ITEMTABPRC.ESTAB = NFCAB.ESTAB AND ITEMTABPRC.TABPRC = NFCAB.TABPRC
            LEFT JOIN
                NFITEM ON NFITEM.SEQNOTA = NFCAB.SEQNOTA AND NFITEM.ESTAB = NFCAB.ESTAB
            LEFT JOIN
                PREPRESE ON PREPRESE.REPRESENT = NFCAB.REPRESENT
            JOIN
                NFCFG ON NFCFG.NOTACONF  = NFCAB.NOTACONF 
            WHERE 
                NFCAB.DTEMISSAO BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD')
                AND TO_DATE('{end_date}', 'YYYY-MM-DD')
            AND
                 NFCFG.ENTRADASAIDA IN 'S'
                {additional_condition}
                {additional_condition_emp}
                {additional_condition_cfg_ped}
                {additional_condition_tab}
            GROUP BY
                CASE
                    WHEN LENGTH(contamov.CNPJF) = 11 THEN 'CPF'
                    WHEN LENGTH(contamov.CNPJF) = 14 THEN 'CNPJ'
                    ELSE 'Outro'
                END
    """
    df = pd.read_sql(query, conn) 
    
    # Formata a coluna 'TOTAL_VENDAS' para o padrão monetário brasileiro
    df['TOTAL_VENDAS_formatado'] = df['TOTAL_VENDAS'].apply(formatar_para_moeda_brasileira)
    df['hover_text'] = df['TIPODOCUMENTO'] + '<br>Total Vendas: ' + df['TOTAL_VENDAS'].apply(formatar_para_moeda_brasileira)

    return {
        'data': [
            {
                'x': df['TIPODOCUMENTO'],
                'y': df['TOTAL_VENDAS'],
                'type': 'bar',
                'text': df['hover_text'].tolist(),
                'hoverinfo': 'text',
                'marker': {'color': '#17BECF'},  # Cor das barras adaptada para o tema escuro
            }
        ],
        'layout': {
            'title': {
                'text': 'Total de Vendas por CPF e CNPJ',
                'font': {'color': 'white'},  # Cor do título adaptada para o tema escuro
            },
            'xaxis': {
                'title': 'CPF/CNPJ',
                'title_font': {'color': 'white'},  # Ajustes de cor para o eixo X
                'tickfont': {'color': 'white'},  # Cor dos ticks do eixo X
            },
            'yaxis': {
                'title': 'Total de Vendas',
                'title_font': {'color': 'white'},  # Ajustes de cor para o eixo Y
                'tickfont': {'color': 'white'},  # Cor dos ticks do eixo Y
            },
            'hovermode': 'closest',
            'paper_bgcolor': '#222',  # Cor de fundo do gráfico para combinar com o tema DARKLY
            'plot_bgcolor': '#222',   # Cor de fundo da área de plotagem para combinar com o tema DARKLY
            'margin': {'l': 40, 'r': 40, 't': 40, 'b': 100},
            'dragmode': False,
            'scrollZoom': False,
        }
    }