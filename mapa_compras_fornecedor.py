from dash import dcc
import pandas as pd
import locale
from datetime import datetime
import plotly.express as px
from conexao_banco_dados import get_connection

# Definindo local BR
locale.setlocale(locale.LC_ALL, 'pt-BR.UTF8')


# Definindo local BR
locale.setlocale(locale.LC_ALL, 'pt-BR.UTF8')

# Conectar BD
conn = get_connection()

def formatar_para_moeda_brasileira(valor):
    """
    Formata um valor float para o padrão monetário brasileiro.
    Exemplo: 249703.00 se torna 'R$ 249.703,00'
    """
    return locale.currency(valor, grouping=True, symbol=True)

def mapa_compras(start_date,end_date,selected_rep_ids, selected_emp_ids, selected_tabpreco_id, selected_cfgpedido_id):
    # Construção das cláusulas de filtro baseadas nas seleções do usuário
    tab_ids_clause = f"AND ITEMTABPRC.TABPRC IN ({', '.join(f"'{tab_id}'" for tab_id in selected_tabpreco_id)})" if selected_tabpreco_id else ""
    emp_ids_clause = f"AND NFCAB.ESTAB IN ({', '.join(f"'{emp_id}'" for emp_id in selected_emp_ids)})" if selected_emp_ids else ""
    rep_ids_clause = f"AND PREPRESE.REPRESENT IN ({', '.join(f"'{rep_id}'" for rep_id in selected_rep_ids)})" if selected_rep_ids else ""
    cfg_ids_clause = f"AND NFCAB.NOTACONF IN ({', '.join(f"'{cfg_ped}'" for cfg_ped in selected_cfgpedido_id)})" if selected_cfgpedido_id else ""

    # Montagem da consulta SQL com as cláusulas de filtro, incluindo a subconsulta para ITEMTABPRC
    query = f"""
    SELECT
        CONTAMOV.LATITUDEENDERECO,
        CONTAMOV.LONGITUDEENDERECO,
        CONTAMOV.NOME,
        CONTAMOV.ENDERECO,
        PREPRESE.DESCRICAO,
        NFITEM.VALORTOTAL,
        NFCAB.DTEMISSAO,
        NFCAB.ESTAB
    FROM
        CONTAMOV
    JOIN
        NFCAB ON CONTAMOV.NUMEROCM = NFCAB.NUMEROCM
	JOIN
        PREPRESE ON PREPRESE.REPRESENT = NFCAB.REPRESENT
    JOIN
        NFCFG ON NFCFG.NOTACONF = NFCAB.NOTACONF
	LEFT JOIN
        ITEMTABPRC ON ITEMTABPRC.ESTAB = NFCAB.ESTAB AND ITEMTABPRC.TABPRC = NFCAB.TABPRC 
	LEFT JOIN
        NFITEM ON NFITEM.SEQNOTA = NFCAB.SEQNOTA AND NFITEM.ESTAB = NFCAB.ESTAB
    WHERE
         NFCAB.DTEMISSAO BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD') AND TO_DATE('{end_date}', 'YYYY-MM-DD')
        AND NFCFG.ENTRADASAIDA = 'E'
        {rep_ids_clause}
        {emp_ids_clause}
        {cfg_ids_clause}
        {tab_ids_clause}
    """
    # Executa a consulta SQL
    df = pd.read_sql(query, conn)

    # Concatena o nome e o endereço para exibição no hover
    df['DTEMISSAO'] = pd.to_datetime(df['DTEMISSAO'])  # Garante que está no formato datetime
    df['hover_text'] = ('Cliente: ' + df['NOME'] + "</br>" +
                    'Endereço: ' + df['ENDERECO'] + "</br>" +
                    'Valor: ' + df['VALORTOTAL'].apply(formatar_para_moeda_brasileira) + "</br>" +
                    'Data Emissão: ' + df['DTEMISSAO'].dt.strftime('%d-%m-%Y') + "</br>"
                    'Estabelecimento: ' + df['ESTAB'].astype(str) + "</br>")

    return df

def create_layout(dataframe):
    if dataframe.empty:
        # Retorna uma mensagem ou um layout alternativo quando não há dados
        return dcc.Graph(
            figure={
                'layout': {
                    'paper_bgcolor': '#343a40',
                    'plot_bgcolor': '#343a40',
                    'font': {'color': '#7FDBFF'},
                    'title': 'Não há dados para exibir.'
                }
            }
        )

    # Se o dataframe não estiver vazio, prossegue com a criação do mapa
    figura = px.scatter_mapbox(
        dataframe,
        hover_name="hover_text",
        color_discrete_sequence=["fuchsia"],  # Considere ajustar as cores para melhorar a visibilidade no tema DARKLY
        zoom=3,
        height=300
    )

    figura.update_layout(
        mapbox_style="carto-darkmatter",  # Estilo de mapa que se encaixa melhor em temas escuros
        margin={"r":0, "t":0, "l":0, "b":0},
        paper_bgcolor='#343a40',  # Fundo do gráfico ajustado para o tema DARKLY
        plot_bgcolor='#343a40',  # Fundo da área de plotagem ajustado para o tema DARKLY
        font={'color': '#7FDBFF'}  # Cor do texto ajustada para melhor contraste no tema DARKLY
    )
    
    return dcc.Graph(id='container-mapa-compras', figure=figura)
