"""Streamlit dashboard for the Peñita FIFA World Cup 2026 porra.

Run:
    pip install streamlit pandas
    streamlit run penita_streamlit_app.py
"""
from __future__ import annotations

import html
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st

from penita_core import (
    GROUP_COLORS,
    build_powerbi_tables,
    build_sample_csv_text,
    load_wide_csv,
    pretty_label,
    pretty_team,
)

st.set_page_config(
    page_title="Peñita FIFA World Cup 2026",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ──────────────────────────────────────────────
# CSS
# ──────────────────────────────────────────────

def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root{
          --bg:#1F2023;
          --bg-alt:#17181B;
          --panel:#2A2B2F;
          --panel-2:#33353A;
          --panel-3:#202126;
          --line:#4A4D55;
          --gold:#C9A24D;
          --gold-2:#E0B95B;
          --text:#F5F5F5;
          --text-soft:#D9D9D9;
          --muted:#B8B8B8;
          --pending:#8F9399;
          --success:#6FCF97;
          --error:#EB5757;
          --warning:#FFB020;
        }
        [data-testid="stAppViewContainer"]{
          background:
            radial-gradient(1200px 700px at 12% -10%, rgba(201,162,77,.18), transparent 55%),
            radial-gradient(900px 500px at 110% 5%, rgba(58,134,255,.15), transparent 50%),
            linear-gradient(180deg, #1c1d20 0%, var(--bg) 22%, var(--bg-alt) 100%);
        }
        [data-testid="stSidebar"]{
          background:linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.02)), var(--panel-3);
          border-right:1px solid rgba(255,255,255,.06);
        }
        .hero{
          border:1px solid rgba(255,255,255,.07);
          background:
            radial-gradient(circle at top right, rgba(201,162,77,.15), transparent 35%),
            linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.02)),
            var(--panel-3);
          border-radius:22px;
          padding:22px 24px;
          margin-bottom:16px;
        }
        .hero h1{
          margin:0;
          color:var(--text);
          font-size:2.4rem;
          line-height:1;
          font-family:"Arial Black", Impact, "Segoe UI", sans-serif;
        }
        .hero p{
          color:var(--text-soft);
          margin:10px 0 0;
          font-size:1rem;
        }
        .badge-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
        .badge{
          display:inline-flex;align-items:center;gap:6px;
          padding:6px 10px;border-radius:999px;
          font-size:.72rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
          border:1px solid rgba(255,255,255,.08);
          color:var(--text-soft);background:rgba(255,255,255,.05);
        }
        .badge.gold{background:rgba(201,162,77,.14);border-color:rgba(201,162,77,.28);color:var(--gold-2)}
        .panel{
          border:1px solid rgba(255,255,255,.07);
          background:linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.015)), var(--panel);
          border-radius:22px;
          padding:16px 18px;
          margin-bottom:16px;
        }
        .panel h3{
          margin:0 0 8px;
          font-size:1.45rem;
          line-height:1.1;
          color:var(--text);
          font-family:"Arial Black", Impact, "Segoe UI", sans-serif;
        }
        .panel p{margin:0;color:var(--text-soft)}
        .podium{display:grid;grid-template-columns:1fr 1.15fr 1fr;gap:10px;align-items:end;margin-top:14px}
        .step{border-radius:18px 18px 10px 10px;padding:14px 12px;text-align:center;border:1px solid rgba(255,255,255,.08)}
        .step strong{display:block;font-size:1.6rem;font-family:"Arial Black", Impact, "Segoe UI", sans-serif;color:white}
        .step .name{margin-top:6px;font-weight:800;color:white}
        .step .pts{margin-top:6px;font-size:.85rem;color:var(--text-soft)}
        .step.first{background:linear-gradient(180deg, rgba(201,162,77,.36), rgba(201,162,77,.10)), var(--panel-2);border-color:rgba(201,162,77,.32);min-height:132px}
        .step.second{background:linear-gradient(180deg, rgba(191,195,204,.28), rgba(191,195,204,.08)), var(--panel-2);min-height:108px}
        .step.third{background:linear-gradient(180deg, rgba(183,122,74,.24), rgba(183,122,74,.08)), var(--panel-2);min-height:96px}
        .bar-row{display:grid;grid-template-columns:48px minmax(120px, 1.5fr) minmax(180px, 5fr) 70px;gap:10px;align-items:center;margin:10px 0;padding:10px 12px;border-radius:16px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06)}
        .bar-row.selected{outline:2px solid rgba(201,162,77,.28)}
        .bar-row.compare{outline:2px solid rgba(58,134,255,.24)}
        .rank-chip{display:grid;place-items:center;width:36px;height:36px;border-radius:12px;background:rgba(255,255,255,.06);font-family:"Arial Black", Impact, "Segoe UI", sans-serif;color:white}
        .bar-track{height:14px;border-radius:999px;background:rgba(255,255,255,.06);overflow:hidden;position:relative}
        .bar-fill{position:absolute;left:0;top:0;bottom:0;border-radius:999px;background:linear-gradient(90deg, var(--gold), var(--gold-2))}
        .bar-fill.compare{background:linear-gradient(90deg, #3A86FF, #4CC9F0)}
        .bar-fill.selected{background:linear-gradient(90deg, var(--gold), #3A86FF)}
        .metric-box{border:1px solid rgba(255,255,255,.06);padding:12px;border-radius:16px;background:rgba(255,255,255,.03)}
        .metric-label{font-size:.74rem;letter-spacing:.08em;text-transform:uppercase;color:var(--text-soft);font-weight:800}
        .metric-value{font-size:1.8rem;font-family:"Arial Black", Impact, "Segoe UI", sans-serif;color:white;margin-top:8px;line-height:1}
        .muted{color:var(--muted)}
        .group-chip-wrap{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
        .group-chip{padding:8px 10px;border-radius:999px;font-size:.75rem;font-weight:800;border:1px solid rgba(255,255,255,.08);background:rgba(255,255,255,.04);color:white}
        .group-chip.warn{box-shadow:0 0 0 1px rgba(255,176,32,.26) inset}
        .mini-legend{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
        .pill{display:inline-flex;align-items:center;gap:6px;padding:6px 10px;border-radius:999px;font-size:.72rem;font-weight:800;border:1px solid rgba(255,255,255,.08)}
        .pill.hit{background:rgba(111,207,151,.12);border-color:rgba(111,207,151,.22);color:var(--success)}
        .pill.warn{background:rgba(255,176,32,.12);border-color:rgba(255,176,32,.22);color:var(--warning)}
        .pill.pending{background:rgba(143,147,153,.14);border-color:rgba(143,147,153,.22);color:var(--pending)}
        .duel-grid{display:grid;grid-template-columns:1fr auto 1fr;gap:12px;align-items:stretch}
        .duel-side{border:1px solid rgba(255,255,255,.06);background:rgba(255,255,255,.03);border-radius:18px;padding:14px}
        .duel-side.leading{border-color:rgba(201,162,77,.28)}
        .duel-name{font-size:1.25rem;font-weight:800;color:white}
        .duel-total{font-size:3rem;font-family:"Arial Black", Impact, "Segoe UI", sans-serif;color:white;line-height:1;margin-top:12px}
        .duel-center{min-width:220px;border:1px solid rgba(201,162,77,.22);background:linear-gradient(180deg, rgba(201,162,77,.12), rgba(201,162,77,.03)), var(--panel);border-radius:18px;padding:16px;text-align:center;display:flex;flex-direction:column;justify-content:center}
        .duel-center strong{font-size:2.6rem;font-family:"Arial Black", Impact, "Segoe UI", sans-serif;color:white;line-height:1}
        .duel-bar{height:16px;border-radius:999px;background:rgba(255,255,255,.06);position:relative;overflow:hidden;margin-top:8px}
        .duel-bar span{position:absolute;top:0;bottom:0}
        .duel-left{right:50%;background:linear-gradient(270deg, rgba(201,162,77,1), rgba(201,162,77,.45));border-radius:999px}
        .duel-right{left:50%;background:linear-gradient(90deg, rgba(58,134,255,.95), rgba(76,201,240,.7));border-radius:999px}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────
# Cache helpers
# ──────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def load_tables_from_text(text: str) -> Dict[str, pd.DataFrame]:
    wide = load_wide_csv(text)
    return build_powerbi_tables(wide)


@st.cache_data(show_spinner=False)
def sample_csv() -> str:
    return build_sample_csv_text()


# ──────────────────────────────────────────────
# HTML helpers  (evitan f-strings con comillas
# anidadas, que rompen en Python < 3.12)
# ──────────────────────────────────────────────

def _step_html(css_class: str, rank_label: str, row: Optional[pd.Series]) -> str:
    name = html.escape(str(row["Participante"])) if row is not None else "—"
    pts  = int(row["TOTAL_PUNTOS"]) if row is not None else 0
    return (
        f"<div class='step {css_class}'>"
        f"<strong>{rank_label}</strong>"
        f"<div class='name'>{name}</div>"
        f"<div class='pts'>{pts} pts</div>"
        f"</div>"
    )


def _duel_side_html(row: pd.Series, is_leading: bool) -> str:
    leading_class = "leading" if is_leading else ""
    name  = html.escape(str(row["Participante"]))
    rank  = int(row["RANKING"])
    total = int(row["TOTAL_PUNTOS"])
    return (
        f"<div class='duel-side {leading_class}'>"
        f"<div class='duel-name'>{name}</div>"
        f"<div class='muted'>#{rank} en el ranking</div>"
        f"<div class='duel-total'>{total}</div>"
        f"</div>"
    )


def _pill_dob_html(row: pd.Series) -> str:
    pill_class = "pill warn" if not bool(row["DOB_Valido"]) else "pill hit"
    return f"<span class='{pill_class}'>{html.escape(str(row['DOB_Warning']))}</span>"


# ──────────────────────────────────────────────
# Render sections
# ──────────────────────────────────────────────

def render_kpi_row(ranking: pd.DataFrame, kpi: Dict) -> None:
    leader = ranking.iloc[0]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Líder actual", leader["Participante"], f"{int(leader['TOTAL_PUNTOS'])} pts")
    c2.metric("Media",        f"{ranking['TOTAL_PUNTOS'].mean():.1f}")
    c3.metric("Dispersión",   f"{ranking['TOTAL_PUNTOS'].std(ddof=0):.1f}")
    c4.metric("Participantes", len(ranking))
    c5.metric("Bote total",   f"{int(kpi['BOTE_TOTAL'])}€")


def render_podium(ranking: pd.DataFrame) -> None:
    top3 = ranking.head(3)
    p = [top3.iloc[i] if len(top3) > i else None for i in range(3)]

    st.markdown(
        "<div class='panel'>"
        "<h3>Podio actual</h3>"
        "<p>El bote total se reparte entre los tres primeros.</p>"
        "<div class='podium'>"
        + _step_html("second", "2º", p[1])
        + _step_html("first",  "1º", p[0])
        + _step_html("third",  "3º", p[2])
        + "</div></div>",
        unsafe_allow_html=True,
    )


def render_top10(ranking: pd.DataFrame, selected: str, compare: Optional[str]) -> None:
    top10 = ranking.head(10).copy()
    max_points = max(int(top10["TOTAL_PUNTOS"].max()), 1)
    pieces: List[str] = [
        "<div class='panel'>"
        "<h3>Top 10</h3>"
        "<p>Barras de impacto para leer la pelea por arriba de un vistazo.</p>"
    ]
    for _, row in top10.iterrows():
        participant = str(row["Participante"])
        classes    = ["bar-row"]
        fill_class = "bar-fill"
        if participant == selected:
            classes.append("selected")
            fill_class += " selected"
        elif compare and participant == compare:
            classes.append("compare")
            fill_class += " compare"
        width = int((int(row["TOTAL_PUNTOS"]) / max_points) * 100)
        row_class = " ".join(classes)
        pieces.append(
            f"<div class='{row_class}'>"
            f"<div class='rank-chip'>{int(row['RANKING'])}</div>"
            f"<div><strong>{html.escape(participant)}</strong></div>"
            f"<div class='bar-track'><span class='{fill_class}' style='width:{width}%'></span></div>"
            f"<div style='text-align:right;font-weight:900'>{int(row['TOTAL_PUNTOS'])}</div>"
            f"</div>"
        )
    pieces.append("</div>")
    st.markdown("".join(pieces), unsafe_allow_html=True)


def render_participant_detail(
    selected_row: pd.Series,
    selected_dob: pd.DataFrame,
) -> None:
    st.markdown(
        "<div class='panel'>"
        "<h3>Detalle de participante</h3>"
        "<p>Todo lo importante del participante activo: puntos, DOB, grupos y picks especiales.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    d1, d2, d3, d4, d5 = st.columns(5)
    d1.metric("Puntos totales", int(selected_row["TOTAL_PUNTOS"]),    f"#{int(selected_row['RANKING'])}")
    d2.metric("Fase de grupos", int(selected_row["PUNTOS_FASE_DE_GRUPOS"]))
    d3.metric("Fase final",     int(selected_row["PUNTOS_FASE_FINAL"]))
    d4.metric("Especiales",     int(selected_row["PUNTOS_ESPECIALES"]))
    d5.metric("DOB ganados",    int(selected_row["DOB_GANADOS"]),     f"{int(selected_row['DOB_WARNINGS'])} alertas")

    comp1, comp2 = st.columns([1.2, 1], gap="large")
    with comp1:
        st.subheader("Composición de puntos")
        blocks = [
            ("Grupos",      int(selected_row["PUNTOS_FASE_DE_GRUPOS"])),
            ("Fase final",  int(selected_row["PUNTOS_FASE_FINAL"])),
            ("Especiales",  int(selected_row["PUNTOS_ESPECIALES"])),
        ]
        total_points = max(int(selected_row["TOTAL_PUNTOS"]), 1)
        for label, value in blocks:
            pct = int((value / total_points) * 100)
            st.progress(pct / 100, text=f"{label}: {value} pts · {pct}%")

    with comp2:
        st.subheader("Resumen de aciertos")
        hit1, hit2, hit3 = st.columns(3)
        hit1.metric("Aciertos",   int(selected_row["ACIERTOS"]))
        hit2.metric("Fallos",     int(selected_row["FALLOS"]))
        hit3.metric("Pendientes", int(selected_row["PENDIENTES"]))
        warnings_df = selected_dob.loc[~selected_dob["DOB_Valido"]]
        if not warnings_df.empty:
            warning_text = ", ".join(
                f"Grupo {g} ({w})"
                for g, w in zip(warnings_df["Grupo"], warnings_df["DOB_Warning"])
            )
            st.warning(f"DOB inconsistente en: {warning_text}")
        else:
            st.success("DOB en regla en todos los grupos.")


def render_dob_chips(selected_dob: pd.DataFrame) -> None:
    st.subheader("Estado DOB por grupo")
    chip_parts: List[str] = ["<div class='group-chip-wrap'>"]
    for _, row in selected_dob.sort_values("Grupo").iterrows():
        group   = str(row["Grupo"])
        warning = str(row["DOB_Warning"])
        color   = GROUP_COLORS[group]
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        style   = (
            f"background:rgba({r},{g},{b},.16);"
            f"border-color:rgba({r},{g},{b},.48);"
            f"color:white;"
        )
        cls = "group-chip warn" if not bool(row["DOB_Valido"]) else "group-chip"
        chip_parts.append(
            f"<span class='{cls}' style='{style}'>{group} · {html.escape(warning)}</span>"
        )
    chip_parts.append("</div>")
    st.markdown("".join(chip_parts), unsafe_allow_html=True)


def render_group_detail(
    active_group: str,
    selected_matches: pd.DataFrame,
    selected_positions: pd.DataFrame,
    selected_specials: pd.DataFrame,
    selected_blocks: pd.DataFrame,
    active_group_row: pd.Series,
) -> None:
    st.subheader(f"Grupo {active_group} · picks y puntos")
    g1, g2 = st.columns([1.3, 1], gap="large")
    with g1:
        st.caption("Partidos del grupo")
        show_matches = selected_matches[["Partido", "RTO", "UNO_X_DOS", "DOB", "PTOS", "Estado"]].copy()
        st.dataframe(show_matches, use_container_width=True, hide_index=True)
    with g2:
        st.caption("Posiciones del grupo")
        show_positions = (
            selected_positions[["EquipoBonito", "Posicion", "PTOS", "Estado"]]
            .copy()
            .rename(columns={"EquipoBonito": "Equipo"})
        )
        st.dataframe(show_positions, use_container_width=True, hide_index=True)

    dob_pill_class = "warn" if not bool(active_group_row["DOB_Valido"]) else "hit"
    st.markdown(
        f"<div class='mini-legend'>"
        f"<span class='pill hit'>{int(active_group_row['PuntosGrupo'])} pts</span>"
        f"<span class='pill'>{int(active_group_row['Aciertos'])} aciertos</span>"
        f"<span class='pill pending'>{int(active_group_row['Pendientes'])} pendientes</span>"
        f"<span class='pill {dob_pill_class}'>{html.escape(str(active_group_row['DOB_Warning']))}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.subheader("Picks especiales")
    show_specials = (
        selected_specials[["Especial", "PickBonito", "PTOS", "Estado"]]
        .copy()
        .rename(columns={"PickBonito": "Pick"})
    )
    st.dataframe(show_specials, use_container_width=True, hide_index=True)


def render_vs_all(
    ranking: pd.DataFrame,
    selected_row: pd.Series,
    selected_blocks: pd.DataFrame,
    selected: str,
    compare: Optional[str],
) -> None:
    st.markdown(
        "<div class='panel'><h3>Participante vs todos</h3>"
        "<p>Posición relativa, diferencias frente a la media y bloque por bloque.</p></div>",
        unsafe_allow_html=True,
    )
    va1, va2, va3 = st.columns([1, 1, 1.2], gap="large")
    with va1:
        st.metric("Posición",            f"#{int(selected_row['RANKING'])} / {len(ranking)}")
        st.metric("Vs media",            f"{float(selected_row['VS_MEDIA']):+.1f}")
        st.metric("Vs líder",            f"{int(selected_row['VS_LIDER']):+d}")
    with va2:
        st.metric("Percentil",           int(selected_row["PERCENTIL"]))
        st.metric("Bloques sobre media", int(selected_row["BLOQUES_SOBRE_MEDIA"]))
        st.metric("Bloques bajo media",  int(selected_row["BLOQUES_BAJO_MEDIA"]))
    with va3:
        dist_df = ranking[["Participante", "TOTAL_PUNTOS"]].copy().sort_values("TOTAL_PUNTOS")
        dist_df["marker"] = dist_df["Participante"].apply(
            lambda v: "Seleccionado" if v == selected else ("Rival" if compare and v == compare else "")
        )
        st.caption("Distribución de puntos")
        st.dataframe(dist_df, use_container_width=True, hide_index=True)

    st.caption("Bloques frente a la media")
    block_view = selected_blocks[["Bloque", "Valor", "MediaBloque", "DeltaVsMedia"]].copy()
    block_view["Valor"]        = block_view["Valor"].round(0).astype(int)
    block_view["MediaBloque"]  = block_view["MediaBloque"].round(2)
    block_view["DeltaVsMedia"] = block_view["DeltaVsMedia"].round(2)
    st.dataframe(block_view, use_container_width=True, hide_index=True)


def render_duel(
    selected_row: pd.Series,
    compare_row: Optional[pd.Series],
    selected: str,
    compare: Optional[str],
) -> None:
    st.markdown(
        "<div class='panel'><h3>Participante vs participante</h3>"
        "<p>Comparación 1v1 clara para ver quién manda en cada bloque.</p></div>",
        unsafe_allow_html=True,
    )
    if compare_row is None:
        st.info("Elige un rival en la comparativa 1v1 para activar el duelo.")
        return

    left, right = selected_row, compare_row
    duel_metrics = [
        ("Total",      int(left["TOTAL_PUNTOS"]),          int(right["TOTAL_PUNTOS"])),
        ("Grupos",     int(left["PUNTOS_FASE_DE_GRUPOS"]),  int(right["PUNTOS_FASE_DE_GRUPOS"])),
        ("Fase final", int(left["PUNTOS_FASE_FINAL"]),      int(right["PUNTOS_FASE_FINAL"])),
        ("Especiales", int(left["PUNTOS_ESPECIALES"]),      int(right["PUNTOS_ESPECIALES"])),
        ("DOB",        int(left["DOB_GANADOS"]),            int(right["DOB_GANADOS"])),
    ]
    left_wins  = sum(1 for _, lv, rv in duel_metrics if lv > rv)
    right_wins = sum(1 for _, lv, rv in duel_metrics if rv > lv)
    diff_total = int(left["TOTAL_PUNTOS"] - right["TOTAL_PUNTOS"])

    if left_wins > right_wins:
        leader_name = str(left["Participante"])
    elif right_wins > left_wins:
        leader_name = str(right["Participante"])
    else:
        leader_name = "Duelo igualado"

    left_leads  = int(left["TOTAL_PUNTOS"])  >= int(right["TOTAL_PUNTOS"])
    right_leads = int(right["TOTAL_PUNTOS"]) > int(left["TOTAL_PUNTOS"])

    st.markdown(
        "<div class='duel-grid'>"
        + _duel_side_html(left, left_leads)
        + f"<div class='duel-center'>"
          f"<strong>{diff_total:+d}</strong>"
          f"<span>{html.escape(leader_name)} manda en {max(left_wins, right_wins)} de {len(duel_metrics)} bloques.</span>"
          f"</div>"
        + _duel_side_html(right, right_leads)
        + "</div>",
        unsafe_allow_html=True,
    )

    for label, left_value, right_value in duel_metrics:
        maximum     = max(left_value, right_value, 1)
        left_width  = int((left_value  / maximum) * 50)
        right_width = int((right_value / maximum) * 50)
        if left_value > right_value:
            winner = selected
        elif right_value > left_value:
            winner = compare
        else:
            winner = "Empate"
        st.markdown(f"**{label}** · {winner}")
        st.markdown(
            f"<div class='duel-bar'>"
            f"<span class='duel-left'  style='width:{left_width}%'></span>"
            f"<span class='duel-right' style='width:{right_width}%'></span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        mc = st.columns(3)
        mc[0].metric(selected, left_value)
        mc[1].metric("Dif.", abs(left_value - right_value))
        mc[2].metric(compare or "Rival", right_value)


def render_global_ranking(
    ranking: pd.DataFrame,
    final_detail: pd.DataFrame,
    selected: str,
    compare: Optional[str],
) -> None:
    st.markdown(
        "<div class='panel'><h3>Ranking global</h3>"
        "<p>Clasificación completa con focos de DOB y diferencias frente al líder.</p></div>",
        unsafe_allow_html=True,
    )
    ranking_filter = st.radio("Filtro de tabla", ["Todos", "Solo activo", "Solo duelo"], horizontal=True)

    def apply_filter(df: pd.DataFrame) -> pd.DataFrame:
        if ranking_filter == "Solo activo":
            return df[df["Participante"] == selected]
        if ranking_filter == "Solo duelo":
            names = [selected] + ([compare] if compare else [])
            return df[df["Participante"].isin(names)]
        return df

    ranking_view = apply_filter(ranking.copy())
    show_ranking = ranking_view[[
        "RANKING", "Participante", "TOTAL_PUNTOS",
        "PUNTOS_FASE_DE_GRUPOS", "PUNTOS_FASE_FINAL",
        "PUNTOS_ESPECIALES", "DOB_GANADOS", "VS_LIDER", "DOB_WARNINGS",
    ]].copy()
    st.dataframe(show_ranking, use_container_width=True, hide_index=True)

    st.markdown(
        "<div class='panel'><h3>Tabla final detallada completa</h3>"
        "<p>Lista final con el detalle requerido de todos los participantes.</p></div>",
        unsafe_allow_html=True,
    )
    detail_view = apply_filter(final_detail.copy())
    sort_col = st.selectbox(
        "Ordenar tabla final por",
        ["Participante", "Puntos Totales", "Puntos Fase de Grupos", "Puntos Fase Final", "Puntos Especiales"],
        index=1,
    )
    sort_ascending = sort_col == "Participante"
    detail_view = detail_view.sort_values(sort_col, ascending=sort_ascending, kind="mergesort")
    st.dataframe(detail_view, use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main() -> None:
    inject_css()

    # ── Session state ───────────────────────────
    if "active_group" not in st.session_state:
        st.session_state.active_group = "A"

    # ── Sidebar: carga de datos ─────────────────
    st.sidebar.markdown("## Peñita FIFA World Cup 2026")
    st.sidebar.caption("Versión Python / Streamlit lista para ajustar manualmente.")

    uploaded    = st.sidebar.file_uploader("Cargar CSV", type=["csv"])
    source_name = "Muestra integrada"
    source_text = sample_csv()
    if uploaded is not None:
        source_name = uploaded.name
        source_text = uploaded.getvalue().decode("utf-8-sig", errors="ignore")

    tables      = load_tables_from_text(source_text)
    ranking     = tables["fact_ranking"].copy()
    final_detail = tables["final_detail"].copy()
    kpi         = tables["kpi_summary"].iloc[0].to_dict()

    participants = ranking["Participante"].tolist()
    if not participants:
        st.error("No hay participantes en el CSV.")
        st.stop()

    # ── Sidebar: controles de navegación ────────
    selected = st.sidebar.selectbox("Participante activo", participants, index=0)
    remaining = ["Sin rival"] + [n for n in participants if n != selected]
    compare_raw = st.sidebar.selectbox(
        "Comparativa 1v1", remaining, index=1 if len(remaining) > 1 else 0
    )
    compare: Optional[str] = None if compare_raw == "Sin rival" else compare_raw

    active_group: str = st.sidebar.radio(
        "Grupo activo",
        options=list(GROUP_COLORS.keys()),
        horizontal=True,
        index=list(GROUP_COLORS.keys()).index(st.session_state.active_group),
    )
    st.session_state.active_group = active_group

    # ── Sidebar: descargas ──────────────────────
    dl1, dl2 = st.sidebar.columns(2)
    with dl1:
        st.download_button(
            "Descargar muestra",
            data=source_text if source_name == "Muestra integrada" else sample_csv(),
            file_name="penita_world_cup_2026_sample.csv",
            mime="text/csv",
        )
    with dl2:
        st.download_button(
            "Ranking JSON",
            data=ranking.to_json(orient="records", force_ascii=False, indent=2),
            file_name="penita_world_cup_2026_ranking.json",
            mime="application/json",
        )

    # ── Hero ────────────────────────────────────
    st.markdown(
        f"<div class='hero'>"
        f"<h1>Peñita FIFA World Cup 2026</h1>"
        f"<p>Dashboard en Python para seguir la porra, cargar tu CSV real y dejarlo listo para iterar.</p>"
        f"<div class='badge-row'>"
        f"<span class='badge gold'>{html.escape(source_name)}</span>"
        f"<span class='badge'>{len(ranking)} participantes</span>"
        f"<span class='badge'>Bote {int(kpi['BOTE_TOTAL'])}€</span>"
        f"<span class='badge'>Grupo activo {html.escape(active_group)}</span>"
        f"</div></div>",
        unsafe_allow_html=True,
    )

    # ── Datos derivados ─────────────────────────
    selected_rows = ranking.loc[ranking["Participante"] == selected]
    if selected_rows.empty:
        st.error(f"No se encontró el participante '{selected}'.")
        st.stop()
    selected_row = selected_rows.iloc[0]

    compare_row: Optional[pd.Series] = None
    if compare:
        compare_rows = ranking.loc[ranking["Participante"] == compare]
        if not compare_rows.empty:
            compare_row = compare_rows.iloc[0]

    selected_groups    = tables["fact_group_summary"].query("Participante == @selected").copy()
    selected_dob       = tables["fact_dob_validation"].query("Participante == @selected").copy()
    selected_matches   = tables["fact_group_matches"].query("Participante == @selected and Grupo == @active_group").copy()
    selected_positions = tables["fact_group_positions"].query("Participante == @selected and Grupo == @active_group").copy()
    selected_specials  = tables["fact_special_picks"].query("Participante == @selected").copy()
    selected_blocks    = tables["fact_block_metrics"].query("Participante == @selected").copy()

    group_rows = selected_groups.query("Grupo == @active_group")
    if group_rows.empty:
        st.warning(f"No hay datos para el grupo {active_group} del participante seleccionado.")
        st.stop()
    active_group_row = group_rows.iloc[0]

    # ── Secciones ───────────────────────────────
    render_kpi_row(ranking, kpi)

    podium_col, top_col = st.columns([1, 1.4], gap="large")
    with podium_col:
        render_podium(ranking)
    with top_col:
        render_top10(ranking, selected, compare)

    render_participant_detail(selected_row, selected_dob)
    render_dob_chips(selected_dob)
    render_group_detail(
        active_group, selected_matches, selected_positions,
        selected_specials, selected_blocks, active_group_row,
    )
    render_vs_all(ranking, selected_row, selected_blocks, selected, compare)
    render_duel(selected_row, compare_row, selected, compare)
    render_global_ranking(ranking, final_detail, selected, compare)

    with st.expander("Notas para ajuste manual"):
        st.markdown(
            """
            - El CSV de entrada se lee respetando exactamente los nombres de columnas definidos en la porra.
            - Las celdas vacías se tratan como pendientes.
            - La validación DOB exige exactamente un `TRUE` por grupo y participante.
            - La lógica de tablas está preparada para reutilizar el mismo modelo en Power BI.
            """
        )


if __name__ == "__main__" or True:
    main()
