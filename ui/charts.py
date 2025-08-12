import plotly.express as px
import streamlit as st
from i18n import MONTHS

def saldo_chart(df_saldo, lang: str, currency: str, title: str):
    if df_saldo.empty:
        st.info("Keine Daten für den gewählten Filter." if lang=="de" else "No data for the selected filter.")
        return
    df_saldo["Monatsname"] = df_saldo["month"].apply(lambda x: f"{MONTHS[lang][int(x.split('-')[1])]} {x.split('-')[0]}")
    fig = px.line(
        df_saldo,
        x="month",
        y="saldo",
        markers=True,
        labels={"saldo": f"Kontostand ({currency})" if lang == "de" else f"Balance ({currency})"},
        title=title,
        hover_name="Monatsname",
        hover_data={"saldo": ":.2f", "month": False},
    )
    fig.update_traces(
        hovertemplate="<b>%{customdata[0]}</b><br>" + f"{currency} " + "%{y:.2f}<extra></extra>",
        customdata=df_saldo[["Monatsname"]].values
    )
    fig.update_layout(
        autosize=True, height=600,
        margin=dict(l=40, r=40, t=80, b=40),
        yaxis=dict(autorange=True, fixedrange=False),
        xaxis=dict(autorange=True, fixedrange=False)
    )
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})