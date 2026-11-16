import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any

CHART_THEME_COLORWAY = ["#4F46E5", "#06B6D4", "#10B981", "#F59E0B", "#EC4899", "#8B5CF6", "#64748B"]


def create_facts_by_predicate_chart(pred_dict: Dict[str, int]):
    if not pred_dict:
        return go.Figure()
    df = pd.DataFrame(list(pred_dict.items()), columns=["Predicate", "Count"])
    df = df.sort_values(by="Count", ascending=True)

    fig = px.bar(
        df,
        x="Count",
        y="Predicate",
        orientation="h",
        color="Count",
        color_continuous_scale="Viridis",
        title="Facts Count by Predicate"
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=35, b=10),
        height=320,
        font=dict(family="Inter, sans-serif"),
        coloraxis_showscale=False
    )
    fig.update_xaxes(showgrid=True, gridcolor="#F1F5F9")
    fig.update_yaxes(showgrid=False)
    return fig


def create_base_vs_inferred_chart(base_count: int, inferred_count: int):
    labels = ["Base Facts", "Inferred Facts"]
    values = [base_count, inferred_count]
    colors = ["#4F46E5", "#10B981"]

    fig = go.Figure(data=[
        go.Pie(
            labels=labels,
            values=values,
            hole=0.6,
            marker=dict(colors=colors),
            textinfo="label+value+percent",
            hoverinfo="label+value"
        )
    ])
    fig.update_layout(
        title="Knowledge Base Composition",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=35, b=10),
        height=320,
        font=dict(family="Inter, sans-serif"),
        showlegend=False
    )
    return fig


def create_students_per_dept_chart(dept_dict: Dict[str, int]):
    if not dept_dict:
        return go.Figure()
    df = pd.DataFrame(list(dept_dict.items()), columns=["Department", "Students"])

    fig = px.bar(
        df,
        x="Department",
        y="Students",
        color="Department",
        color_discrete_sequence=CHART_THEME_COLORWAY,
        title="Students per Department"
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=35, b=10),
        height=280,
        font=dict(family="Inter, sans-serif"),
        showlegend=False
    )
    fig.update_yaxes(showgrid=True, gridcolor="#F1F5F9")
    fig.update_xaxes(showgrid=False)
    return fig


def create_courses_per_prof_chart(prof_dict: Dict[str, int]):
    if not prof_dict:
        return go.Figure()
    df = pd.DataFrame(list(prof_dict.items()), columns=["Professor", "Courses"])

    fig = px.bar(
        df,
        x="Professor",
        y="Courses",
        color="Courses",
        color_continuous_scale="Teal",
        title="Courses Taught per Professor"
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=35, b=10),
        height=280,
        font=dict(family="Inter, sans-serif"),
        coloraxis_showscale=False
    )
    fig.update_yaxes(showgrid=True, gridcolor="#F1F5F9")
    fig.update_xaxes(showgrid=False)
    return fig
