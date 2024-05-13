from dash import dcc
import pandas as pd
import locale
from datetime import datetime
import plotly.express as px
from conexao_banco_dados import get_connection

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

def mapa_vendas(start_date=None, end_date=None, selected_reps_ids=None,selected_emp_ids=None,selected_tabpreco_id=None, selected_cfgpedido_id=None):

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
        additional_condition_cfg_ped = f" AND NFCFG.NOTACONF IN ({cfg_pedido_str})"
    else:
        additional_condition_cfg_ped = ""


    # Definições de data, se necessário
    if start_date is None or end_date is None:
        end_date = datetime.today().strftime('%Y-%m-%d')
        start_date = (datetime.today() - pd.DateOffset(months=1)).strftime('%Y-%m-%d')

    # Inicializa additional_conditional vazio para uso na consulta
    additional_conditional = ""
    # Verifica se há representantes selecionados e se a lista não está vazia
    if selected_reps_ids and len(selected_reps_ids) > 0:
        rep_ids_str = ", ".join(f"'{rep_id}'" for rep_id in selected_reps_ids)
        additional_conditional += f" AND PREPRESE.REPRESENT IN ({rep_ids_str})"

    # Modifica a consulta para remover a condição que sempre falha quando selected_reps_ids é vazio
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
    	NFCAB
	LEFT JOIN
        NFITEM ON NFITEM.SEQNOTA = NFCAB.SEQNOTA AND NFITEM.ESTAB = NFCAB.ESTAB
	LEFT JOIN
        ITEMTABPRC ON ITEMTABPRC.ESTAB = NFCAB.ESTAB AND ITEMTABPRC.TABPRC = NFCAB.TABPRC        
    LEFT JOIN
        CONTAMOV ON CONTAMOV.NUMEROCM = NFCAB.NUMEROCM 
	JOIN
        PREPRESE ON PREPRESE.REPRESENT = NFCAB.REPRESENT
    JOIN
        NFCFG ON NFCFG.NOTACONF = NFCAB.NOTACONF
    WHERE
		NFCFG.ENTRADASAIDA IN 'S'
    AND
		NFCAB.DTEMISSAO BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD') 
        AND TO_DATE('{end_date}', 'YYYY-MM-DD')
        {additional_condition_emp}
        {additional_conditional}
        {additional_condition_cfg_ped}
        {additional_condition_tab}
    """
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
    
    return dcc.Graph(id='container-mapa-vendas', figure=figura)
