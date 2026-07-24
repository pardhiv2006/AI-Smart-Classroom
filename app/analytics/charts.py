"""
ScholarMind AI — Analytics Charts
Plotly-based visualizations for quiz trends, subject performance,
study activity heatmap, and topic mastery.
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import random


# ─────────────────────────────────────────────────────────────────
# SHARED STYLE
# ─────────────────────────────────────────────────────────────────

def _base_layout(title: str, theme: str = "Light Modern") -> dict:
    """Base Plotly layout config adapted to current theme."""
    is_dark = theme in ("Dark Mode", "Cyber Theme")
    bg = "rgba(0,0,0,0)" 
    text_color = "#1A1A2E" if not is_dark else "#E2E8F0"
    grid_color = "rgba(0,0,0,0.06)" if not is_dark else "rgba(255,255,255,0.06)"
    return dict(
        title=dict(text=title, font=dict(size=15, family="Plus Jakarta Sans, Inter, sans-serif", color=text_color)),
        paper_bgcolor=bg,
        plot_bgcolor=bg,
        font=dict(family="Plus Jakarta Sans, Inter, sans-serif", color=text_color, size=11),
        xaxis=dict(gridcolor=grid_color, zerolinecolor=grid_color),
        yaxis=dict(gridcolor=grid_color, zerolinecolor=grid_color),
        margin=dict(l=30, r=30, t=50, b=30),
        showlegend=True,
        legend=dict(font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
    )


# ─────────────────────────────────────────────────────────────────
# 1. QUIZ SCORE TREND
# ─────────────────────────────────────────────────────────────────

def quiz_score_trend_chart(quiz_history: list[dict], theme: str = "Light Modern") -> go.Figure:
    """
    Line chart showing quiz score % over time.
    quiz_history: list of {book_name, score, total, difficulty, timestamp}
    """
    if not quiz_history:
        df = pd.DataFrame({
            "Date": pd.date_range(end=datetime.now(), periods=7, freq="D"),
            "Score %": [random.randint(40, 95) for _ in range(7)],
            "Book": ["Sample Book"] * 7,
        })
    else:
        df = pd.DataFrame(quiz_history)
        df["Score %"] = (df["score"] / df["total"] * 100).round(1)
        df["Date"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("Date")
        df.rename(columns={"book_name": "Book"}, inplace=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Date"], y=df["Score %"],
        mode="lines+markers",
        name="Quiz Score",
        line=dict(color="#6366F1", width=2.5, shape="spline"),
        marker=dict(size=7, color="#6366F1", line=dict(width=2, color="#fff")),
        fill="tozeroy",
        fillcolor="rgba(99,102,241,0.08)",
        hovertemplate="<b>%{x|%b %d}</b><br>Score: %{y:.1f}%<extra></extra>",
    ))

    layout = _base_layout("📈 Quiz Score Trend", theme)
    layout["yaxis"]["range"] = [0, 105]
    layout["yaxis"]["ticksuffix"] = "%"
    fig.update_layout(**layout)
    return fig


# ─────────────────────────────────────────────────────────────────
# 2. SUBJECT PERFORMANCE RADAR
# ─────────────────────────────────────────────────────────────────

def subject_performance_radar(quiz_history: list[dict], theme: str = "Light Modern") -> go.Figure:
    """Radar chart showing performance by book/subject."""
    is_dark = theme in ("Dark Mode", "Cyber Theme")

    if not quiz_history:
        subjects = ["Mathematics", "Physics", "History", "Chemistry", "Literature"]
        scores = [72, 85, 60, 90, 45]
    else:
        df = pd.DataFrame(quiz_history)
        df["Score %"] = (df["score"] / df["total"] * 100).round(1)
        grouped = df.groupby("book_name")["Score %"].mean().reset_index()
        subjects = grouped["book_name"].str[:20].tolist()
        scores = grouped["Score %"].round(1).tolist()

    # Close the radar
    subjects_closed = subjects + [subjects[0]]
    scores_closed = scores + [scores[0]]

    line_color = "#00FFFF" if theme == "Cyber Theme" else "#6366F1"
    fill_color = "rgba(0,255,255,0.12)" if theme == "Cyber Theme" else "rgba(99,102,241,0.12)"

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=scores_closed, theta=subjects_closed,
        fill="toself", fillcolor=fill_color,
        line=dict(color=line_color, width=2),
        name="Performance",
        hovertemplate="<b>%{theta}</b><br>Score: %{r:.1f}%<extra></extra>",
    ))

    text_color = "#E2E8F0" if is_dark else "#1A1A2E"
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], ticksuffix="%",
                            gridcolor="rgba(128,128,128,0.2)", color=text_color),
            angularaxis=dict(gridcolor="rgba(128,128,128,0.2)", color=text_color),
            bgcolor="rgba(0,0,0,0)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        title=dict(text="🎯 Subject Performance", font=dict(size=15, color=text_color,
                   family="Plus Jakarta Sans, Inter, sans-serif")),
        font=dict(family="Plus Jakarta Sans, Inter, sans-serif", color=text_color),
        margin=dict(l=50, r=50, t=60, b=30),
        showlegend=False,
    )
    return fig


# ─────────────────────────────────────────────────────────────────
# 3. STUDY ACTIVITY HEATMAP (GitHub-style calendar)
# ─────────────────────────────────────────────────────────────────

def study_activity_heatmap(study_sessions: list[dict], theme: str = "Light Modern") -> go.Figure:
    """
    Calendar heatmap of study activity over the last 12 weeks.
    study_sessions: list of {start_time: ISO str}
    """
    is_dark = theme in ("Dark Mode", "Cyber Theme")

    # Build 84-day (12 weeks) date grid
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=83)
    all_dates = pd.date_range(start=start_date, end=end_date, freq="D")

    activity = {d.date(): 0 for d in all_dates}
    for session in study_sessions:
        try:
            d = datetime.fromisoformat(session["start_time"]).date()
            if d in activity:
                activity[d] += 1
        except Exception:
            pass

    dates = list(activity.keys())
    values = list(activity.values())
    df = pd.DataFrame({"date": dates, "count": values})
    df["week"] = [(d - start_date).days // 7 for d in dates]
    df["weekday"] = [d.weekday() for d in dates]
    df["label"] = [d.strftime("%b %d") for d in dates]

    colorscale = "Blues" if not is_dark else [[0, "#0A0E1A"], [1, "#06B6D4"]]
    if theme == "Cyber Theme":
        colorscale = [[0, "#050510"], [1, "#00FFFF"]]
    elif theme == "Pastel Theme":
        colorscale = [[0, "#FDF6F9"], [1, "#EC4899"]]

    fig = go.Figure(go.Heatmap(
        x=df["week"], y=df["weekday"], z=df["count"],
        colorscale=colorscale,
        showscale=False,
        text=df["label"],
        customdata=df["count"],
        hovertemplate="<b>%{text}</b><br>Sessions: %{customdata}<extra></extra>",
        xgap=3, ygap=3,
    ))

    text_color = "#E2E8F0" if is_dark else "#1A1A2E"
    fig.update_layout(
        title=dict(text="📅 Study Activity (Last 12 Weeks)", font=dict(size=15, color=text_color, family="Plus Jakarta Sans, Inter, sans-serif")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=text_color, family="Plus Jakarta Sans, Inter, sans-serif"),
        yaxis=dict(tickvals=[0,1,2,3,4,5,6], ticktext=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],
                   gridcolor="rgba(0,0,0,0)"),
        xaxis=dict(showticklabels=False, gridcolor="rgba(0,0,0,0)"),
        margin=dict(l=40, r=20, t=50, b=20),
        height=200,
    )
    return fig


# ─────────────────────────────────────────────────────────────────
# 4. TOPIC MASTERY PROGRESS BARS
# ─────────────────────────────────────────────────────────────────

def topic_mastery_chart(quiz_history: list[dict], theme: str = "Light Modern") -> go.Figure:
    """Horizontal bar chart showing mastery per book/topic."""
    is_dark = theme in ("Dark Mode", "Cyber Theme")
    text_color = "#E2E8F0" if is_dark else "#1A1A2E"

    if not quiz_history:
        topics = ["Deep Learning", "Computer Networks", "Algorithms", "Data Structures"]
        scores = [88, 62, 75, 45]
    else:
        df = pd.DataFrame(quiz_history)
        df["Score %"] = (df["score"] / df["total"] * 100).round(1)
        grouped = df.groupby("book_name")["Score %"].mean().reset_index()
        topics = grouped["book_name"].str[:25].tolist()
        scores = grouped["Score %"].round(1).tolist()

    # Color by mastery level
    bar_colors = []
    for s in scores:
        if s >= 80:
            bar_colors.append("#059669")
        elif s >= 60:
            bar_colors.append("#6366F1")
        elif s >= 40:
            bar_colors.append("#D97706")
        else:
            bar_colors.append("#DC2626")

    fig = go.Figure(go.Bar(
        y=topics, x=scores,
        orientation="h",
        marker_color=bar_colors,
        text=[f"{s:.0f}%" for s in scores],
        textposition="outside",
        textfont=dict(color=text_color),
        hovertemplate="<b>%{y}</b><br>Mastery: %{x:.1f}%<extra></extra>",
    ))

    layout = _base_layout("🧠 Topic Mastery", theme)
    layout["xaxis"]["range"] = [0, 115]
    layout["xaxis"]["ticksuffix"] = "%"
    layout["yaxis"]["automargin"] = True
    layout["height"] = max(200, len(topics) * 50 + 80)
    layout["showlegend"] = False
    fig.update_layout(**layout)
    return fig


# ─────────────────────────────────────────────────────────────────
# 5. DIFFICULTY BREAKDOWN PIE
# ─────────────────────────────────────────────────────────────────

def difficulty_breakdown_pie(quiz_history: list[dict], theme: str = "Light Modern") -> go.Figure:
    """Pie chart showing quiz attempts by difficulty level."""
    is_dark = theme in ("Dark Mode", "Cyber Theme")
    text_color = "#E2E8F0" if is_dark else "#1A1A2E"

    if not quiz_history:
        labels = ["Beginner", "Intermediate", "Advanced"]
        values = [3, 7, 2]
    else:
        df = pd.DataFrame(quiz_history)
        grouped = df["difficulty"].value_counts().reset_index()
        labels = grouped["difficulty"].tolist()
        values = grouped["count"].tolist()

    colors = ["#34D399", "#6366F1", "#F43F5E"]

    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.5,
        marker=dict(colors=colors, line=dict(color="rgba(0,0,0,0)", width=2)),
        textinfo="label+percent",
        textfont=dict(color=text_color, size=11),
        hovertemplate="<b>%{label}</b><br>Quizzes: %{value}<br>%{percent}<extra></extra>",
    ))

    fig.update_layout(
        title=dict(text="⚡ Quiz by Difficulty", font=dict(size=15, color=text_color, family="Plus Jakarta Sans, Inter, sans-serif")),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans, Inter, sans-serif", color=text_color),
        margin=dict(l=20, r=20, t=50, b=20),
        showlegend=True,
        legend=dict(font=dict(color=text_color, size=10), bgcolor="rgba(0,0,0,0)"),
    )
    return fig
