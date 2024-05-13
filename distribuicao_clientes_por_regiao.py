import pandas as pd
import locale
import plotly.express as px
from conexao_banco_dados import get_connection
from dash import dcc


# Definindo local BR
locale.setlocale(locale.LC_ALL, 'pt-BR.UTF8')

# Conectar BD
conn = get_connection()

def mapa_regiao():
    query = """ 
            SELECT 
                CONTAMOV.NUMEROCM,
                CONTAMOV.NOME,
                CIDADE.NOME AS CIDADE_NOME,
                CIDADE.UF,
                PAIS.NOME AS PAIS_NOME,
                CONTAMOV.LATITUDEENDERECO,
                CONTAMOV.LONGITUDEENDERECO 
            FROM 
                contamov 
            JOIN CIDADE ON contamov.CIDADE = CIDADE.CIDADE 
            JOIN PAIS ON CIDADE.PAIS = PAIS.PAIS 
    """
    df = pd.read_sql(query, conn)
    return df

def create_layout(dataframe):
    if dataframe.empty:
        # Retorna uma mensagem ou um layout alternativo quando não há dados
        return dcc.Graph(
            figure={
                'layout': {
                    'xaxis': {
                        'visible': False
                    },
                    'yaxis': {
                        'visible': False
                    },
                    'annotations': [{
                        'text': 'Não há dados para exibir.',
                        'xref': 'paper',
                        'yref': 'paper',
                        'showarrow': False,
                        'font': {
                            'size': 28,
                            'color': '#7FDBFF'
                        }
                    }],
                    'paper_bgcolor': '#343a40',
                    'plot_bgcolor': '#343a40',
                    'font': {'color': '#7FDBFF'}
                }
            }
        )

    # Se o dataframe não estiver vazio, prossegue com a criação do mapa
    figura = px.scatter_mapbox(
        dataframe,
        lat='LATITUDEENDERECO',
        lon='LONGITUDEENDERECO',
        hover_name="NOME",  # Este campo deve existir no seu DataFrame
        hover_data=["CIDADE_NOME", "UF", "PAIS_NOME"],  # Informações adicionais para exibir no hover
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
    
    return dcc.Graph(id='container-mapa-clientes-regiao', figure=figura)
