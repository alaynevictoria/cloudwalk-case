import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.spines.right"] = False

NAVY = "#1B2A4A"
TEAL = "#2E8B8B"
CORAL = "#E07856"
GREY = "#9AA5B1"
CHARTS = "/home/claude/cloudwalk-sourcing-analysis/outputs/charts"

d = json.load(open("/home/claude/cloudwalk-sourcing-analysis/dashboard/data.json"))

# 1. FUNNEL
fig, ax = plt.subplots(figsize=(8, 4.5))
steps = list(d["funnel"].keys())
vals = list(d["funnel"].values())
bars = ax.barh(steps[::-1], vals[::-1], color=NAVY, height=0.6)
for b, v in zip(bars, vals[::-1]):
    ax.text(v + 8, b.get_y() + b.get_height() / 2, str(v), va="center", fontsize=10, color=NAVY)
ax.set_xlabel("Candidatos")
ax.set_title("Funil de Sourcing — CloudWalk (jan-jun 2025)", fontsize=13, weight="bold", loc="left")
ax.set_xlim(0, max(vals) * 1.15)
plt.tight_layout()
plt.savefig(f"{CHARTS}/01_funil.png", dpi=150)
plt.close()

# 2. CONVERSION BY CHANNEL
fig, ax = plt.subplots(figsize=(8, 4.5))
rows = sorted(d["by_channel"], key=lambda r: r["rate"], reverse=True)
labels = [r["source_channel"] for r in rows]
rates = [r["rate"] for r in rows]
colors = [TEAL if r >= rates[len(rates)//2] else GREY for r in rates]
bars = ax.bar(labels, rates, color=colors)
for b, r in zip(bars, rates):
    ax.text(b.get_x() + b.get_width()/2, r + 0.15, f"{r}%", ha="center", fontsize=9)
ax.set_ylabel("Taxa de contratação (%)")
ax.set_title("Conversão por canal de sourcing", fontsize=13, weight="bold", loc="left")
plt.xticks(rotation=30, ha="right")
plt.tight_layout()
plt.savefig(f"{CHARTS}/02_canal.png", dpi=150)
plt.close()

# 3. CONVERSION BY RECRUITER — alphabetical order, single neutral color.
# Deliberately NOT sorted/highlighted by rank: this chart feeds a section about
# practice-sharing opportunities, not individual performance ranking.
fig, ax = plt.subplots(figsize=(7, 4.5))
rows = sorted(d["by_recruiter"], key=lambda r: r["recruiter"])
labels = [r["recruiter"] for r in rows]
rates = [r["rate"] for r in rows]
bars = ax.bar(labels, rates, color="#8891E0")
for b, r in zip(bars, rates):
    ax.text(b.get_x() + b.get_width()/2, r + 0.15, f"{r}%", ha="center", fontsize=9)
ax.set_ylabel("Taxa de contratação (%)")
ax.set_title("Conversão por recrutador(a) — ordem alfabética", fontsize=13, weight="bold", loc="left")
plt.tight_layout()
plt.savefig(f"{CHARTS}/03_recrutador.png", dpi=150)
plt.close()

# 4. SCORES: hired vs not
fig, ax = plt.subplots(figsize=(7, 4.5))
rows = d["scores_by_hired"]
labels = ["Técnico", "Comportamental", "Gestor"]
not_hired = [r for r in rows if r["hired"] == False][0]
hired = [r for r in rows if r["hired"] == True][0]
x = range(len(labels))
w = 0.35
ax.bar([i - w/2 for i in x], [not_hired["technical_test_score"], not_hired["behavior_score"], not_hired["manager_score"]],
       width=w, label="Não contratado", color=GREY)
ax.bar([i + w/2 for i in x], [hired["technical_test_score"], hired["behavior_score"], hired["manager_score"]],
       width=w, label="Contratado", color=NAVY)
ax.set_xticks(list(x))
ax.set_xticklabels(labels)
ax.set_ylabel("Score médio")
ax.set_title("Scores médios: contratados vs. não contratados", fontsize=13, weight="bold", loc="left")
ax.legend(frameon=False)
plt.tight_layout()
plt.savefig(f"{CHARTS}/04_scores.png", dpi=150)
plt.close()

# 5. NOTE SIGNAL CONVERSION (AI classification result)
fig, ax = plt.subplots(figsize=(6.5, 4.5))
rows = sorted(d["signal_conv"], key=lambda r: r["rate"], reverse=True)
label_map = {"positive": "Sinal positivo", "mixed": "Sinal misto", "risk": "Sinal de risco"}
labels = [label_map[r["note_signal"]] for r in rows]
rates = [r["rate"] for r in rows]
colors = [TEAL, CORAL, NAVY]
bars = ax.bar(labels, rates, color=colors)
for b, r in zip(bars, rates):
    ax.text(b.get_x() + b.get_width()/2, r + 0.15, f"{r}%", ha="center", fontsize=9)
ax.set_ylabel("Taxa de contratação (%)")
ax.set_title("Conversão por sinal qualitativo (classificado por IA)", fontsize=12, weight="bold", loc="left")
plt.tight_layout()
plt.savefig(f"{CHARTS}/05_sinal_ia.png", dpi=150)
plt.close()

# 6. PERSIST SCORE DISTRIBUTION
fig, ax = plt.subplots(figsize=(6.5, 4.5))
ps = d["persist_summary"]
keys = sorted(ps.keys())
vals = [ps[k] for k in keys]
bars = ax.bar([f"{k} pt(s)" for k in keys], vals, color=TEAL)
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width()/2, v + 1, str(v), ha="center", fontsize=9)
ax.set_ylabel("Candidatos ativos")
ax.set_title("Distribuição do Persist Score (candidatos em processo)", fontsize=12, weight="bold", loc="left")
plt.tight_layout()
plt.savefig(f"{CHARTS}/06_persist_score.png", dpi=150)
plt.close()

print("charts done")
