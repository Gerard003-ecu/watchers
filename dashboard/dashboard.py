#!/usr/bin/env python3
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import requests
import json
import logging
import numpy as np

# URL del endpoint REST que expone el estado de la malla
MALLA_ENDPOINT = "http://localhost:5000/api/malla"

def obtener_estado_malla():
    """
    Realiza una solicitud GET al endpoint REST para obtener el estado de la malla.
    Retorna un diccionario con la respuesta JSON o un diccionario con error.
    """
    try:
        response = requests.get(MALLA_ENDPOINT, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Error al obtener estado de la malla: {e}")
        return {"error": str(e)}

# Inicializamos la aplicación Dash con Bootstrap para un estilo profesional
external_stylesheets = [dbc.themes.BOOTSTRAP]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Dashboard de Watchers"

# Layout del dashboard
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Dashboard de Estado de la Malla Watchers"), width=12)
    ], className="my-3"),
    
    # Controles interactivos: Slider y Dropdown
    dbc.Row([
        dbc.Col([
            html.Label("Ajuste de lambda_foton (nm):"),
            dcc.Slider(
                id="slider-lambda",
                min=400, max=800, step=10,
                value=600,
                marks={str(i): f"{i} nm" for i in range(400, 810, 50)},
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], width=6),
        dbc.Col([
            html.Label("Seleccionar Malla a Visualizar:"),
            dcc.Dropdown(
                id="dropdown-malla",
                options=[
                    {"label": "Malla A", "value": "malla_A"},
                    {"label": "Malla B", "value": "malla_B"},
                    {"label": "Ambas", "value": "ambas"}
                ],
                value="ambas",
                clearable=False
            )
        ], width=6)
    ], className="my-3"),
    
    # Intervalo para actualización periódica
    dbc.Row([
        dbc.Col(dcc.Interval(id="interval-component", interval=10*1000, n_intervals=0), width=12)
    ]),
    
    # Sección de estado en formato JSON
    dbc.Row([
        dbc.Col(html.Div(id="estado-div"), width=12)
    ], className="my-3"),
    
    # Sección para gráficos (barras y mapa de calor)
    dbc.Row([
        dbc.Col(html.Div(id="grafico-div"), width=12)
    ], className="my-3")
], fluid=True)

# Callback para actualizar el estado de la malla y mostrar el valor actual de lambda_foton
@app.callback(
    Output("estado-div", "children"),
    [Input("interval-component", "n_intervals"),
     Input("slider-lambda", "value")]
)
def actualizar_estado(n_intervals, lambda_value):
    estado = obtener_estado_malla()
    if "error" in estado:
        return html.Div("Error al obtener estado: " + estado["error"], style={"color": "red"})
    # Se agrega el valor de lambda_foton recibido desde el slider
    if "resonador" in estado:
        estado["resonador"]["lambda_foton_actual"] = lambda_value
    else:
        estado["resonador"] = {"lambda_foton_actual": lambda_value}
    return html.Pre(json.dumps(estado, indent=4), style={"backgroundColor": "#f8f9fa", "padding": "10px"})

# Callback para actualizar los gráficos: gráfico de barras y mapa de calor
@app.callback(
    Output("grafico-div", "children"),
    [Input("interval-component", "n_intervals"),
     Input("dropdown-malla", "value")]
)
def actualizar_grafico(n_intervals, malla_seleccionada):
    estado = obtener_estado_malla()
    if not estado or "error" in estado:
        return html.Div("No se pueden mostrar gráficos debido a un error.", style={"color": "red"})
    
    def avg_amplitude(malla):
        total = 0
        count = 0
        for fila in malla:
            for celda in fila:
                total += celda.get("amplitude", 0)
                count += 1
        return total / count if count else 0
    
    # Preparar datos para el gráfico de barras
    data_barras = []
    if malla_seleccionada in ["malla_A", "ambas"]:
        prom_A = avg_amplitude(estado.get("malla_A", []))
        data_barras.append(go.Bar(x=["Malla A"], y=[prom_A], marker_color="blue"))
    if malla_seleccionada in ["malla_B", "ambas"]:
        prom_B = avg_amplitude(estado.get("malla_B", []))
        data_barras.append(go.Bar(x=["Malla B"], y=[prom_B], marker_color="green"))
    
    grafico_barras = dcc.Graph(
        figure=go.Figure(data=data_barras, layout=go.Layout(title="Amplitud Promedio"))
    )
    
    # Preparar datos para el mapa de calor de la malla A (como ejemplo)
    malla_A = estado.get("malla_A", [])
    if malla_A:
        # Convertir la malla en una matriz de amplitudes
        amplitudes = [[celda.get("amplitude", 0) for celda in fila] for fila in malla_A]
        grafico_calor = dcc.Graph(
            figure=go.Figure(
                data=go.Heatmap(z=amplitudes, colorscale="Viridis"),
                layout=go.Layout(title="Mapa de Calor - Malla A")
            )
        )
    else:
        grafico_calor = html.Div("No hay datos para la malla A.")

    return html.Div([grafico_barras, grafico_calor])

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
