import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
import locale
from conexao_banco_dados import get_connection
from datetime import datetime

# Definir a localização para pt_BR
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Estabelecer a conexão com o banco de dados Oracle
conn = get_connection()

# Função para formatar valor para o padrão monetário brasileiro manualmente
def formatar_para_moeda_brasileira(valor):
    """
    Formata um valor float para o padrão monetário brasileiro.
    Exemplo: 249703.00 se torna 'R$ 249.703,00'
    """
    valor_str = f"{valor:,.2f}"
    valor_str = valor_str.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {valor_str}"

def create_layout():
    layout = html.Div(id='container-grafico-vendas-mensais', children=[
        dbc.Row([
            dbc.Col(width=1),  # Coluna vazia para ocupar espaço à esquerda
            dbc.Col(
                dbc.Card([
                    html.Div(
                        [
                            html.H2("Total de Vendas Mensais por Estabelecimento", style={"font-family": "Voltaire", "font-size": "20px", "text-align": "center"}),
                        ],
                        style={"padding": "10px"}
                    ),
                    dbc.Row([
                        dbc.Col([
                            dcc.Graph(
                                id='bar-chart-total-vendas-mensais',
                                config={'displayModeBar': False, 'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian', 'zoom2d', 'zoom3d', 'orbitRotation', 'tableRotation', 'resetCameraDefault3d', 'resetCameraLastSave3d', 'hoverClosest3d', 'zoomInGeo', 'zoomOutGeo', 'resetGeo', 'hoverClosestGeo', 'hoverClosestGl2d', 'hoverClosestPie', 'toggleHover', 'resetViews', 'resetViewMapbox']}
                            )
                        ], width=12)
                    ])
                ]), width=12
            ),
            dbc.Col(width=1),  # Coluna vazia para ocupar espaço à direita
        ])
    ])
    
    return layout

def update_chart(start_date, end_date, selected_rep_ids,selected_emp_ids, selected_tabpreco_id,selected_cfgpedido_id):

    # Define o período padrão para o mês atual, caso não seja fornecido
    if start_date is None or end_date is None:
        hoje = datetime.now()
        primeiro_dia_do_mes = hoje.replace(day=1).strftime('%Y-%m-%d')
        ultimo_dia_do_mes = hoje.strftime('%Y-%m-%d')
    else:
        primeiro_dia_do_mes = datetime.strptime(start_date, '%Y-%m-%d').strftime('%Y-%m-%d')
        ultimo_dia_do_mes = datetime.strptime(end_date, '%Y-%m-%d').strftime('%Y-%m-%d')

    if selected_emp_ids:
        emp_ids_str = ", ".join(f"'{emp_id}'" for emp_id in selected_emp_ids)
        additional_condition_emp = f" AND NFCAB.ESTAB IN ({emp_ids_str})"
    else:
        additional_condition_emp = ""


    if selected_rep_ids:
        rep_ids_str = ", ".join(f"'{rep_id}'" for rep_id in selected_rep_ids)
        additional_condition = f" AND PREPRESE.REPRESENT IN ({rep_ids_str})"
    else:
        additional_condition = ""


    # Verifica se há algum ID de tabela de preço selecionado e prepara a condição
    if selected_tabpreco_id:
        tab_ids_str = ", ".join(f"'{tab_id}'" for tab_id in selected_tabpreco_id)
        additional_condition_tab = f" AND ITEMTABPRC.TABPRC IN ({tab_ids_str})"
    else:
        additional_condition_tab = ""

    if selected_cfgpedido_id:
        cfg_pedido_str = ", ".join(f"'{tab_id}'" for tab_id in selected_cfgpedido_id)
        additional_condition_cfg_ped = f" AND NFCFG.NOTACONF IN ({cfg_pedido_str})"
    else:
        additional_condition_cfg_ped = ""


    

    # Executa a consulta SQL
    query = f"""
        SELECT
                pempresa.FANTASIA,
                pempresa.EMPRESA,
                TRUNC(MAX(NFCAB.DTEMISSAO)) AS data_pedido,
                SUM(NFITEM.VALORTOTAL) AS total_vendas
            FROM
                NFCAB
            JOIN
                pempresa ON NFCAB.ESTAB = pempresa.EMPRESA
            LEFT JOIN
                PREPRESE ON PREPRESE.REPRESENT = NFCAB.REPRESENT
            LEFT JOIN
                ITEMTABPRC ON ITEMTABPRC.ESTAB = NFCAB.ESTAB AND ITEMTABPRC.TABPRC = NFCAB.TABPRC
            LEFT JOIN
                NFITEM ON NFITEM.SEQNOTA = NFCAB.SEQNOTA AND NFITEM.ESTAB = NFCAB.ESTAB
            JOIN
                NFCFG ON NFCFG.NOTACONF = NFCAB.NOTACONF
            WHERE
                NFCAB.DTEMISSAO BETWEEN TO_DATE(:primeiro_dia_do_mes, 'YYYY-MM-DD') AND TO_DATE(:ultimo_dia_do_mes, 'YYYY-MM-DD')
                {additional_condition_emp}
                {additional_condition}
                {additional_condition_cfg_ped}
                {additional_condition_tab}
                AND NFCFG.ENTRADASAIDA IN 'S'
            GROUP BY 
                pempresa.FANTASIA,
                pempresa.EMPRESA
            ORDER BY 
                TO_NUMBER(pempresa.EMPRESA)
    """
    df = pd.read_sql(query, conn, params={'primeiro_dia_do_mes': primeiro_dia_do_mes, 'ultimo_dia_do_mes': ultimo_dia_do_mes})
    df['EMPRESA'] = df['EMPRESA'].astype(str)


    # Formata a coluna 'TOTAL_VENDAS' para o padrão monetário brasileiro
    df['hover_text'] = df['FANTASIA'] + '<br>Total Vendas: ' + df['TOTAL_VENDAS'].apply(formatar_para_moeda_brasileira)

    # Preparando os dados do gráfico
    return {
        'data': [
            {
                'x': df['FANTASIA'].tolist(),
                'y': df['TOTAL_VENDAS'].tolist(),
                'type': 'bar',
                'text': df['hover_text'].tolist(),
                'hoverinfo': 'text',
                'marker': {'color': '#17BECF'},  # Cor das barras adaptada para o tema escuro
            }
        ],
        'layout': {
            'title': {
                'text': 'Total de Vendas Mensais por Estabelecimento',
                'font': {'color': 'white'},  # Cor do título adaptada para o tema escuro
            },
            'xaxis': {
                'title': 'Estabelecimento',
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