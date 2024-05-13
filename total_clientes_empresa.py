import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
import locale
from conexao_banco_dados import get_connection

# Definir o local BR
locale.setlocale(locale.LC_ALL, 'pt-BR.UTF8')

# Conectar BD
conn = get_connection()

def buscar_total_clientes():
    query = "SELECT COUNT(NUMEROCM) AS Total_Cliente FROM CONTAMOV"
    df = pd.read_sql(query, conn)
    return df['TOTAL_CLIENTE'].iloc[0]
    

def create_layout():
    total_clientes = buscar_total_clientes()  # Busca o total de clientes
    layout = html.Div(id='container-total-clientes-empresa', children=[
        dbc.Row([
            dbc.Col(width=1),
            dbc.Col(
                dbc.Card([
                    html.H2('Total de Clientes na Empresa', style={"font-family": "Voltaire", "font-size": "20px", "text-align": "center"}),
                    html.H3(f'Total de Clientes: {total_clientes}', style={"text-align": "center"})  # Exibe o total de clientes aqui
                ],
                    style={"padding":"10px"}
                ),
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(
                            id='bar-chart-total-clientes-empresa',
                        )
                    ])
                ]), width=4
            ), dbc.Col(width=1),
        ])
    ])
    return layout
