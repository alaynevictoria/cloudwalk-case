"""
CloudWalk - Sourcing Funnel Analysis
Core analysis logic. This script is mirrored, cell by cell, into
notebooks/sourcing_funnel_analysis.ipynb and feeds dashboard/data.json.
"""
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "DejaVu Sans"
CHARTS = "/home/claude/cloudwalk-sourcing-analysis/outputs/charts"

df = pd.read_csv("/home/claude/cloudwalk-sourcing-analysis/data/mock_sourcing_dataset.csv",
                  parse_dates=["sourced_date", "first_contact_date", "screening_date",
                               "interview1_date", "test_date", "offer_date", "hired_date"])

# ---------------------------------------------------------------
# 1. FUNNEL
# ---------------------------------------------------------------
funnel_steps = {
    "Sourced": len(df),
    "Respondeu": int(df.response_received.sum()),
    "Screening OK": int(df.screening_pass.sum()),
    "Entrevista OK": int(df.interview1_pass.sum()),
    "Teste realizado": int(df.test_taken.sum()),
    "Oferta enviada": int(df.offer_sent.sum()),
    "Contratado": int(df.hired.sum()),
}

# ---------------------------------------------------------------
# 2. CONVERSION BY DIMENSION (channel / recruiter / seniority / dept / decision source)
# ---------------------------------------------------------------
def conv_table(col):
    g = df.groupby(col)["hired"].agg(hires="sum", total="count")
    g["rate"] = (g["hires"] / g["total"] * 100).round(1)
    return g.sort_values("rate", ascending=False)

by_channel = conv_table("source_channel")
by_recruiter = conv_table("recruiter")
by_seniority = conv_table("seniority")
by_department = conv_table("department")
by_decision = conv_table("decision_source")
by_workmode = conv_table("work_mode")

# ---------------------------------------------------------------
# 3. SCORES & VELOCITY vs HIRED
# ---------------------------------------------------------------
score_cols = ["technical_test_score", "behavior_score", "manager_score"]
scores_by_hired = df.groupby("hired")[score_cols].mean().round(1)
velocity_by_hired = df.groupby("hired")[["response_time_days", "stage_duration_days"]].mean().round(1)

# ---------------------------------------------------------------
# 4. REJECTION REASONS (excluding still-in-process NaNs)
# ---------------------------------------------------------------
rejection_counts = df.rejection_reason.value_counts()

# ---------------------------------------------------------------
# 5. AI-ASSISTED CLASSIFICATION OF recruiter_notes
#    Methodology (documented fully in docs/Relatorio_Tecnico.pdf):
#    the 11 distinct note templates were classified into
#    signal categories by Claude (Anthropic), reading each note's
#    semantic content and tagging it as a positive engagement signal,
#    a risk signal, or a mixed/friction signal. This mirrors how an
#    LLM-based "automated candidate feedback" classifier would run in
#    production (e.g. via the Anthropic Messages API against the
#    recruiter_notes field) - see notebooks/ai_note_classifier.py
#    for the callable, API-ready version of this step.
# ---------------------------------------------------------------
NOTE_CLASSIFICATION = {
    "Baixa responsividade nas etapas iniciais.": {
        "theme": "Risco - Engajamento",
        "signal": "risk",
    },
    "Pediu prazo adicional para retorno.": {
        "theme": "Risco - Indecisao/Timing",
        "signal": "risk",
    },
    "Experiência sólida, mas expectativa salarial alta.": {
        "theme": "Atrito - Expectativa salarial",
        "signal": "mixed",
    },
    "Demonstrou interesse claro na oportunidade.": {
        "theme": "Positivo - Engajamento",
        "signal": "positive",
    },
    "Pontos fortes em execução e autonomia.": {
        "theme": "Positivo - Perfil comportamental",
        "signal": "positive",
    },
    "Perfil técnico acima da média.": {
        "theme": "Positivo - Forca tecnica",
        "signal": "positive",
    },
    "Apresentou aderência forte ao contexto da vaga.": {
        "theme": "Positivo - Fit com a vaga",
        "signal": "positive",
    },
    "Bom potencial de evolução.": {
        "theme": "Positivo - Potencial de crescimento",
        "signal": "positive",
    },
    "Feedback positivo do gestor.": {
        "theme": "Positivo - Endosso do gestor",
        "signal": "positive",
    },
    "Boa comunicação e resposta rápida.": {
        "theme": "Positivo - Comunicacao/responsividade",
        "signal": "positive",
    },
    "Perfil com forte aderência e processo acelerado.": {
        "theme": "Positivo - Fit forte + processo acelerado",
        "signal": "positive",
    },
}

df["note_theme"] = df.recruiter_notes.map(lambda x: NOTE_CLASSIFICATION[x]["theme"])
df["note_signal"] = df.recruiter_notes.map(lambda x: NOTE_CLASSIFICATION[x]["signal"])

signal_conv = conv_table("note_signal")
theme_conv = conv_table("note_theme")

# cache the "AI classification output" as its own artifact (mirrors a real
# pipeline where the classifier's output is persisted for reuse / audit)
notes_classified = df[["candidate_id", "recruiter_notes", "note_theme", "note_signal", "hired"]]
notes_classified.to_csv(
    "/home/claude/cloudwalk-sourcing-analysis/outputs/ai_notes_classification.csv", index=False
)

# ---------------------------------------------------------------
# 6. "WORTH PERSISTING" SCORE
#    Simple, explainable heuristic (not a black box) combining the two
#    strongest behavioural signals found above: quick responsiveness
#    and a positive/mixed note signal, for candidates still active
#    (not yet hired or rejected).
# ---------------------------------------------------------------
active = df[df.final_stage.isin(["Sourced", "Screening", "Interview", "Test", "Offer"])].copy()
median_response = df.response_time_days.median()
median_stage_duration = df.stage_duration_days.median()

def persist_score(row):
    pts = 0
    if pd.notna(row.response_time_days) and row.response_time_days <= median_response:
        pts += 1
    if row.note_signal in ("positive",):
        pts += 1
    if pd.notna(row.technical_test_score) and row.technical_test_score >= 75:
        pts += 1
    if pd.notna(row.manager_score) and row.manager_score >= 75:
        pts += 1
    return pts

active["persist_score"] = active.apply(persist_score, axis=1)
persist_summary = active.persist_score.value_counts().sort_index()

# ---------------------------------------------------------------
# EXPORT everything the dashboard needs
# ---------------------------------------------------------------
export = {
    "funnel": funnel_steps,
    "by_channel": by_channel.reset_index().to_dict("records"),
    "by_recruiter": by_recruiter.reset_index().to_dict("records"),
    "by_seniority": by_seniority.reset_index().to_dict("records"),
    "by_department": by_department.reset_index().to_dict("records"),
    "by_decision": by_decision.reset_index().to_dict("records"),
    "by_workmode": by_workmode.reset_index().to_dict("records"),
    "scores_by_hired": scores_by_hired.reset_index().to_dict("records"),
    "velocity_by_hired": velocity_by_hired.reset_index().to_dict("records"),
    "rejection_counts": rejection_counts.to_dict(),
    "theme_conv": theme_conv.reset_index().to_dict("records"),
    "signal_conv": signal_conv.reset_index().to_dict("records"),
    "persist_summary": {str(k): int(v) for k, v in persist_summary.items()},
    "overall_hire_rate": round(df.hired.mean() * 100, 1),
    "total_candidates": len(df),
    "median_response_time_days": float(median_response),
    "median_stage_duration_days": float(median_stage_duration),
    "channels": sorted(df.source_channel.unique().tolist()),
    "recruiters": sorted(df.recruiter.unique().tolist()),
    "seniorities": ["Junior", "Pleno", "Senior", "Staff"],
    "note_signals": ["positive", "mixed", "risk"],
}
with open("/home/claude/cloudwalk-sourcing-analysis/dashboard/data.json", "w", encoding="utf-8") as f:
    json.dump(export, f, ensure_ascii=False, indent=2)

print(json.dumps(export, ensure_ascii=False, indent=2)[:3000])
