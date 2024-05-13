import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
import locale
from conexao_banco_dados import get_connection

# Definir a localização para pt_BR
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Estabelecer a conexão com o banco de dados Oracle
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



def update_chart(start_date,end_date,selected_rep_ids, selected_emp_ids, selected_tabpreco_id, selected_cfgpedido_id):

    # Construção das cláusulas de filtro baseadas nas seleções do usuário
    tab_ids_clause = f"AND ITEMTABPRC.TABPRC IN ({', '.join(f"'{tab_id}'" for tab_id in selected_tabpreco_id)})" if selected_tabpreco_id else ""
    emp_ids_clause = f"AND NFCAB.ESTAB IN ({', '.join(f"'{emp_id}'" for emp_id in selected_emp_ids)})" if selected_emp_ids else ""
    rep_ids_clause = f"AND PREPRESE.REPRESENT IN ({', '.join(f"'{rep_id}'" for rep_id in selected_rep_ids)})" if selected_rep_ids else ""
    
    query = f""" 
            SELECT
                PEMPRESA.EMPRESA,
                PEMPRESA.FANTASIA AS NOME_FILIAL,
                SUM(NFITEM.VALORTOTAL) AS TOTAL_DEVOLUCAO
            FROM
                NFCAB
            LEFT JOIN
                PREPRESE ON PREPRESE.REPRESENT = NFCAB.REPRESENT
            JOIN
                PEMPRESA ON PEMPRESA.EMPRESA = NFCAB.ESTAB
            JOIN
                NFCFG ON NFCFG.NOTACONF = NFCAB.NOTACONF
            LEFT JOIN
                ITEMTABPRC ON ITEMTABPRC.ESTAB = NFCAB.ESTAB AND ITEMTABPRC.TABPRC = NFCAB.TABPRC
	        JOIN
                NFITEM ON NFITEM.SEQNOTA = NFCAB.SEQNOTA AND NFITEM.ESTAB = NFCAB.ESTAB
            WHERE
                NFCAB.DTEMISSAO BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD')
                AND TO_DATE('{end_date}', 'YYYY-MM-DD')    
                AND NFCAB.NOTACONF IN (2,6)
                {rep_ids_clause}
                {emp_ids_clause}
                {tab_ids_clause}
            GROUP BY
                PEMPRESA.EMPRESA, PEMPRESA.FANTASIA
            ORDER BY
                PEMPRESA.EMPRESA
    """
    
    df = pd.read_sql(query, conn)

    # Adaptações para o tema DARKLY
    empresa = df['NOME_FILIAL'].tolist()
    total_devolucao = df['TOTAL_DEVOLUCAO'].apply(formatar_para_moeda_brasileira).tolist()    

    # Construindo o gráfico
    data = [{
        'x': empresa,
        'y': df['TOTAL_DEVOLUCAO'],
        'type': 'bar',
        'marker': {'color': '#17BECF'},  # Cor adaptada ao tema DARKLY
        'name': 'Total de Devoluções por Filial',
        'text': total_devolucao,
        'hoverinfo': 'text+x'
    }]

    layout = {
        'title': {
            'text': 'Total de Devoluções por Filial',
            'font': {'color': 'white'}  # Cor do título adaptada
        },
        'xaxis': {
            'title': 'Estabelecimento',
            'title_font': {'color': 'white'},  # Cor do título do eixo X
            'tickfont': {'color': 'white'},  # Cor dos ticks do eixo X
            'tickangle': -45
        },
        'yaxis': {
            'title': 'Total de Devolução',
            'title_font': {'color': 'white'},  # Cor do título do eixo Y
            'tickfont': {'color': 'white'},  # Cor dos ticks do eixo Y
            'tickformat': ',.2f'
        },
        'paper_bgcolor': '#222',  # Cor de fundo do gráfico
        'plot_bgcolor': '#222',  # Cor de fundo da área de plotagem
        'margin': {'l': 50, 'r': 50, 't': 50, 'b': 150},
        'dragmode': False,
        'scrollZoom': False
    }

    return {'data': data, 'layout': layout}