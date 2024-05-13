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

def valor_total_saving(start_date,end_date,selected_rep_ids, selected_emp_ids, selected_tabpreco_id, selected_cfgpedido_id):
    # se não receber datas, define um intervalo padrão (exemplo: mes atual)
    if start_date is None or end_date is None:
        end_date = datetime.today().strftime('%Y-%m-%d')
        start_date = (datetime.today() - pd.DateOffset(months=1)).strftime('%Y-%m-%d')

    # Construção das cláusulas de filtro baseadas nas seleções do usuário
    tab_ids_clause = f"AND ITEMTABPRC.TABPRC IN ({', '.join(f"'{tab_id}'" for tab_id in selected_tabpreco_id)})" if selected_tabpreco_id else ""
    emp_ids_clause = f"AND NFCAB.ESTAB IN ({', '.join(f"'{emp_id}'" for emp_id in selected_emp_ids)})" if selected_emp_ids else ""
    rep_ids_clause = f"AND PREPRESE.REPRESENT IN ({', '.join(f"'{rep_id}'" for rep_id in selected_rep_ids)})" if selected_rep_ids else ""

    query = f""" 
WITH UltimaCompra AS (
    SELECT
        NFITEM.ITEM,
        MAX(NFCAB.DTEMISSAO) AS UltimaDataCompra,
        MAX(NFCAB.SEQNOTA) KEEP (DENSE_RANK LAST ORDER BY NFCAB.DTEMISSAO) AS UltimaSeqNota
    FROM
        nfitem
    JOIN
        NFCAB ON NFCAB.SEQNOTA = NFITEM.SEQNOTA
    WHERE
         NFCAB.NOTACONF = 18
    AND
        NFCAB.DTEMISSAO < TO_DATE('{start_date}', 'YYYY-MM-DD')         
    GROUP BY NFITEM.ITEM
),
DetalhesCompra AS (
    SELECT
        nfitem.ESTAB,
        COALESCE(nfitem.CUSTOCMV, 0) AS CustoAquisicaoAtual,
        COALESCE(nfitem.CUSTOCMVP, 0) AS CustoAquisicaoAnterior,
        nfitem.CUSTOUNIT,
        nfitem.CUSTOTOTAL,
        nfitem.ITEM,
        nfitem.SEQNOTA AS SeqNotaAtual,
        NFCAB.VALORPROD,
        B.CustoAnterior,
        B.UltimaSeqNota AS SeqNotaAnterior,+
        (B.CustoAnterior - COALESCE(nfitem.CUSTOCMV, 0)) AS DiferencaCusto,
        (COALESCE(nfitem.CUSTOCMVP, 0) - COALESCE(nfitem.CUSTOCMV, 0)) AS Saving,
        NFCAB.REPRESENT,
        PREPRESE.DESCRICAO AS RepresentanteDescricao
    FROM nfitem
    JOIN NFCAB ON NFCAB.SEQNOTA = NFITEM.SEQNOTA
    LEFT JOIN PREPRESE ON PREPRESE.REPRESENT = NFCAB.REPRESENT
    LEFT JOIN ITEMTABPRC ON ITEMTABPRC.ESTAB = NFCAB.ESTAB AND ITEMTABPRC.TABPRC = NFCAB.TABPRC
    LEFT JOIN NFITEM ON NFITEM.SEQNOTA = NFCAB.SEQNOTA AND NFITEM.ESTAB = NFCAB.ESTAB
    LEFT JOIN NFCFG ON NFCFG.NOTACONF = NFCAB.NOTACONF
    LEFT JOIN (
        SELECT
            NFITEM.ITEM,
            COALESCE(NFITEM.CUSTOCMVP, 0) AS CustoAnterior,
            NFCAB.SEQNOTA AS UltimaSeqNota,
            NFCAB.DTEMISSAO AS DataUltimaCompra
        FROM nfitem
        JOIN NFCAB ON NFCAB.SEQNOTA = NFITEM.SEQNOTA
        JOIN UltimaCompra ON UltimaCompra.ITEM = NFITEM.ITEM AND UltimaCompra.UltimaDataCompra = NFCAB.DTEMISSAO
        AND UltimaCompra.UltimaSeqNota = NFCAB.SEQNOTA
    ) B ON nfitem.ITEM = B.ITEM
    WHERE NFCAB.NOTACONF = 18
      AND NFCAB.DTEMISSAO BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD')
      AND TO_DATE('{end_date}', 'YYYY-MM-DD')
      AND NFCFG.ENTRADASAIDA = 'E'
        {rep_ids_clause}
        {emp_ids_clause}
        {tab_ids_clause}
)
SELECT
    SUM(DiferencaCusto) AS TotalDiferencaCusto,
    SUM(Saving) AS TotalSaving
FROM DetalhesCompra
"""
    df = pd.read_sql(query, conn)
    total_saving = df['TOTALDIFERENCACUSTO'].iloc[0] if not df.empty else 0

    if total_saving is None:
        total_saving = 0
    total_saving_formatado = locale.format_string('%.2f', total_saving, grouping=True)
    return total_saving_formatado


def create_layout():
    total_saving = valor_total_saving()  # busca a soma de todas as vendas realizadas em X periodo
    layout = html.Div(id='container-valor-total-saving', children=[
        dbc.Row([
            dbc.Col(width=1),
            dbc.Col(
                dbc.Card([
                    html.H2('Soma do Total do Saving', style={"font-family": "Voltaire", "font-size": "20px", "text-align": "center"}),
                    # Aqui você exibe o valor já formatado
                    html.H3(f'Soma de Total do Saving: R$ {total_saving}', style={"text-align": "center"})
                ],
                    style={"padding": "10px"}
                ),
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(
                            id='bar-chart-total-saving'
                        )
                    ])
                ]), width=4
            ), dbc.Col(width=1)
        ])
    ])
    return layout