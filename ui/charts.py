import plotly.express as px
import plotly.io as pio
import streamlit as st
from typing import Callable, Optional

from i18n import MONTHS, get_text


def saldo_chart(df_saldo, lang: str, currency: str, title: str, t: Optional[Callable[[str], str]] = None):
    if df_saldo.empty:
        fallback = (lambda k: get_text(lang, k))
        st.info(fallback("chart_no_data"))
        return
    if t is None:
        t = lambda k: get_text(lang, k)
    def _month_label(x: str) -> str:
        try:
            y, m = x.split("-")[:2]
            return f"{MONTHS[lang][int(m)]} {y}"
        except Exception:
            return x
    df_saldo["Monatsname"] = df_saldo["month"].apply(_month_label)
    fig = px.line(
        df_saldo,
        x="month",
        y="saldo",
        markers=True,
        labels={"saldo": t("chart_balance_label").format(currency=currency)},
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

def set_plotly_theme(theme: str):
    pio.templates.default = "plotly_dark" if theme == "dark" else "plotly"