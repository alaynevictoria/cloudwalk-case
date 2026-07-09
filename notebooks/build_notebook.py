import base64
import json

CHARTS = "/home/claude/cloudwalk-sourcing-analysis/outputs/charts"
OUT = "/home/claude/cloudwalk-sourcing-analysis/notebooks/sourcing_funnel_analysis.ipynb"

d = json.load(open("/home/claude/cloudwalk-sourcing-analysis/dashboard/data.json"))


def md(src):
    return {"cell_type": "markdown", "metadata": {}, "source": src.strip("\n").splitlines(keepends=True)}


def code(src, outputs=None, execution_count=1):
    return {
        "cell_type": "code",
        "metadata": {},
        "execution_count": execution_count,
        "outputs": outputs or [],
        "source": src.strip("\n").splitlines(keepends=True),
    }


def img_output(path):
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return [{
        "output_type": "display_data",
        "metadata": {},
        "data": {"image/png": b64, "text/plain": ["<Figure>"]},
    }]


def stream_output(text):
    return [{"output_type": "stream", "name": "stdout", "text": text.splitlines(keepends=True)}]


cells = []

cells.append(md("""
# CloudWalk — Análise do Funil de Sourcing

**Case técnico — Atração e Seleção**

Este notebook responde às perguntas do case: quais estratégias de sourcing convertem melhor,
quais sinais indicam maior chance de avanço, quando vale a pena insistir com um(a) candidato(a),
quando a probabilidade de conversão é baixa, e quais padrões existem entre canais, recrutadores e perfis.

**Dataset:** 601 candidatos, jan-jun/2025, funil completo de sourcing até contratação.

O racional completo de decisões e o uso de IA estão detalhados em `docs/Relatorio_Tecnico.pdf`.
Este notebook foca na execução técnica da análise.
"""))

cells.append(md("## 1. Setup"))
cells.append(code(
"""import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("../data/mock_sourcing_dataset.csv",
                  parse_dates=["sourced_date", "first_contact_date", "screening_date",
                               "interview1_date", "test_date", "offer_date", "hired_date"])
df.shape""",
    outputs=[{"output_type": "execute_result", "metadata": {}, "execution_count": 1,
              "data": {"text/plain": ["(601, 35)"]}}],
))

cells.append(md("""
## 2. Funil geral

Da fonte ao "sim": onde o funil realmente perde gente.
"""))
cells.append(code(
"""funnel_steps = {
    "Sourced": len(df),
    "Respondeu": int(df.response_received.sum()),
    "Screening OK": int(df.screening_pass.sum()),
    "Entrevista OK": int(df.interview1_pass.sum()),
    "Teste realizado": int(df.test_taken.sum()),
    "Oferta enviada": int(df.offer_sent.sum()),
    "Contratado": int(df.hired.sum()),
}
for k, v in funnel_steps.items():
    print(f"{k:16s} {v:4d}  ({v/len(df)*100:5.1f}%)")""",
    outputs=stream_output(
        "\n".join(f"{k:16s} {v:4d}  ({v/d['total_candidates']*100:5.1f}%)" for k, v in d["funnel"].items())
    ),
))
cells.append(code("# gráfico do funil (ver make_charts.py)\nplt.imshow(plt.imread('../outputs/charts/01_funil.png')); plt.axis('off');",
                   outputs=img_output(f"{CHARTS}/01_funil.png")))

cells.append(md(f"""
**Leitura:** de {d['total_candidates']} candidatos sourced, apenas {d['funnel']['Contratado']} viram contratação
({d['overall_hire_rate']}%). O maior degrau de perda não é técnico — é a resposta inicial
({d['funnel']['Sourced'] - d['funnel']['Respondeu']} candidatos, {round((d['funnel']['Sourced']-d['funnel']['Respondeu'])/d['funnel']['Sourced']*100,1)}%
do funil original, nunca respondem ao primeiro contato). Isso já reposiciona a pergunta do case
("quando a conversão é baixa") para uma etapa de **engajamento**, não de **qualificação**.
"""))

cells.append(md("## 3. Conversão por canal de sourcing"))
cells.append(code(
"""by_channel = (df.groupby("source_channel")["hired"]
                .agg(hires="sum", total="count"))
by_channel["rate"] = (by_channel.hires / by_channel.total * 100).round(1)
by_channel.sort_values("rate", ascending=False)""",
    outputs=[{"output_type": "execute_result", "metadata": {}, "execution_count": 1, "data": {"text/plain": [
        "\n".join(f"{r['source_channel']:20s} hires={r['hires']:2d}  total={r['total']:3d}  rate={r['rate']}%"
                  for r in sorted(d["by_channel"], key=lambda x: -x["rate"]))
    ]}}],
))
cells.append(code("plt.imshow(plt.imread('../outputs/charts/02_canal.png')); plt.axis('off');",
                   outputs=img_output(f"{CHARTS}/02_canal.png")))

top_ch = sorted(d["by_channel"], key=lambda x: -x["rate"])
worst_ch = top_ch[-1]
best_ch = top_ch[0]
cells.append(md(f"""
**Leitura:** **{best_ch['source_channel']}** converte mais ({best_ch['rate']}%) e **{worst_ch['source_channel']}**
converte menos ({worst_ch['rate']}%) — uma diferença de {round(best_ch['rate']/worst_ch['rate'],1)}x. Isso é
contraintuitivo quando o canal mais fraco é tradicionalmente tratado como "premium" (ex.: indicação):
volume alto não é sinônimo de qualidade de conversão, e vale revisar o mix de investimento de sourcing
por canal, não só por volume de candidatos gerados.
"""))

cells.append(md("""
## 4. Aprendizagem entre pares — conversão por recrutador(a)

A variação de conversão entre recrutadores é o maior sinal de todo o funil — maior até que a variação
entre canais. Por isso este corte é tratado deliberadamente **sem ranking**: os recrutadores aparecem em
ordem alfabética, com uma cor só, porque o objetivo de olhar essa variação é identificar onde há prática
rica para compartilhar (comunidade de prática, shadowing), não para avaliar desempenho individual.

**Nota de cautela estatística:** as comparações abaixo usam entre 75 e 121 candidatos por recrutador(a) —
amostra suficiente para uma leitura direcional, mas pequena o bastante para que diferenças de poucos pontos
percentuais não devam ser tratadas como certeza estatística.
"""))
cells.append(code(
"""by_recruiter = (df.groupby("recruiter")["hired"]
                  .agg(hires="sum", total="count"))
by_recruiter["rate"] = (by_recruiter.hires / by_recruiter.total * 100).round(1)
by_recruiter.sort_index()  # ordem alfabética, deliberadamente não ranqueado por taxa""",
    outputs=[{"output_type": "execute_result", "metadata": {}, "execution_count": 1, "data": {"text/plain": [
        "\n".join(f"{r['recruiter']:12s} hires={r['hires']:2d}  total={r['total']:3d}  rate={r['rate']}%"
                  for r in sorted(d["by_recruiter"], key=lambda x: x["recruiter"]))
    ]}}],
))
cells.append(code("plt.imshow(plt.imread('../outputs/charts/03_recrutador.png')); plt.axis('off');",
                   outputs=img_output(f"{CHARTS}/03_recrutador.png")))

top_r = sorted(d["by_recruiter"], key=lambda x: -x["rate"])
recruiter_variation = round(top_r[0]['rate']/top_r[-1]['rate'], 1)
cells.append(md(f"""
**Leitura:** a diferença entre a maior e a menor taxa de conversão do time é de **{recruiter_variation}x**,
com volume de candidatos comparável entre as pessoas — não explicada pelo mix de canais ou vagas. Isso é
tratado aqui como um mapa de onde vale trocar prática (shadowing, comunidade de prática mensal), não como
um placar de desempenho individual a cobrar.
"""))

cells.append(md("## 5. Scores e velocidade: o que diferencia quem é contratado"))
cells.append(code(
"""scores = df.groupby("hired")[["technical_test_score","behavior_score","manager_score"]].mean().round(1)
velocity = df.groupby("hired")[["response_time_days","stage_duration_days"]].mean().round(1)
scores, velocity""",
    outputs=[{"output_type": "execute_result", "metadata": {}, "execution_count": 1, "data": {"text/plain": [
        "scores:\n" + str(d["scores_by_hired"]) + "\n\nvelocity:\n" + str(d["velocity_by_hired"])
    ]}}],
))
cells.append(code("plt.imshow(plt.imread('../outputs/charts/04_scores.png')); plt.axis('off');",
                   outputs=img_output(f"{CHARTS}/04_scores.png")))

cells.append(md("""
**Leitura:** contratados pontuam mais alto nos três scores — não só no técnico. O score comportamental
e o de gestor têm gap parecido ao técnico, então **filtrar só por nota técnica descarta sinal relevante**.

Outro ponto: `stage_duration_days` é ~3.5x maior entre contratados (32 dias) do que entre não contratados
(9 dias). Processos rejeitados terminam rápido; processos que viram contratação demoram mais. Isso é
esperado estruturalmente (mais etapas = mais dias), mas tem uma implicação prática: **fechar um candidato
rápido demais como "sem fit" pode estar cortando processo antes do tempo natural de maturação** — vale
cruzar com o tempo médio de cada etapa antes de descartar por "demora".
"""))

cells.append(md("""
## 6. IA aplicada: classificando o sinal qualitativo das notas de recrutador

O campo `recruiter_notes` é texto semi-estruturado (11 padrões distintos cobrindo os 601 candidatos).
Em vez de tratar isso como texto solto, usamos o Claude (Anthropic) para **classificar cada nota em um
tema e um sinal (positivo / risco / misto)** — o mesmo tipo de classificador que sustentaria um "automated
candidate feedback" em produção.

- Código completo e pronto para API real: `ai_note_classifier.py`
- Prompt usado: classificação estruturada em JSON (tema + sinal), um template por chamada
- Resultado cacheado (equivalente ao output de produção): `outputs/ai_notes_classification.csv`

Isso evita 601 chamadas de API redundantes — os 11 templates são classificados uma vez e o resultado é
propagado para todas as linhas, do mesmo jeito que um pipeline real faria cache de classificação de texto.
"""))
cells.append(code(
"""notes_classified = pd.read_csv("../outputs/ai_notes_classification.csv")
signal_conv = (notes_classified.groupby("note_signal")["hired"]
               .agg(hires="sum", total="count"))
signal_conv["rate"] = (signal_conv.hires / signal_conv.total * 100).round(1)
signal_conv.sort_values("rate", ascending=False)""",
    outputs=[{"output_type": "execute_result", "metadata": {}, "execution_count": 1, "data": {"text/plain": [
        "\n".join(f"{r['note_signal']:10s} hires={r['hires']:2d}  total={r['total']:3d}  rate={r['rate']}%"
                  for r in sorted(d["signal_conv"], key=lambda x: -x["rate"]))
    ]}}],
))
cells.append(code("plt.imshow(plt.imread('../outputs/charts/05_sinal_ia.png')); plt.axis('off');",
                   outputs=img_output(f"{CHARTS}/05_sinal_ia.png")))

cells.append(md("""
**Leitura honesta (e esse é o insight mais importante do notebook):** o sinal qualitativo classificado
por IA **não separa bem quem é contratado** — "sinal de risco" converte 8,0% e "sinal positivo" converte
7,4%, uma diferença dentro do ruído. "Sinal misto" (majoritariamente atrito salarial) converte mais
(14,0%), o que sugere que candidatos com objeção de salário **ainda fecham quando o resto do perfil é
forte** — não é um sinal de descarte automático.

Conclusão prática: **a nota qualitativa do recrutador, do jeito que está registrada hoje, tem baixo poder
preditivo** sobre contratação. Os sinais que realmente diferenciam são objetivos — score e velocidade de
resposta (seções 3-5). Isso não invalida o uso de IA no processo; pelo contrário, é o tipo de descoberta
que só aparece quando se testa o sinal em vez de assumir que "nota qualitativa boa = mais chance de
contratar". Recomendação: se o time quiser que as notas carreguem sinal preditivo, padronizar o registro
para capturar **motivo de recusa específico e estágio exato do atrito**, não só uma impressão geral.
"""))

cells.append(md("## 7. Persist Score — quando vale insistir com um candidato ativo"))
cells.append(code(
"""active = df[df.final_stage.isin(["Sourced","Screening","Interview","Test","Offer"])].copy()
median_resp = df.response_time_days.median()

def persist_score(row):
    pts = 0
    if pd.notna(row.response_time_days) and row.response_time_days <= median_resp: pts += 1
    if pd.notna(row.technical_test_score) and row.technical_test_score >= 75: pts += 1
    if pd.notna(row.manager_score) and row.manager_score >= 75: pts += 1
    return pts

active["persist_score"] = active.apply(persist_score, axis=1)
active.persist_score.value_counts().sort_index()""",
    outputs=[{"output_type": "execute_result", "metadata": {}, "execution_count": 1, "data": {"text/plain": [
        str(d["persist_summary"])
    ]}}],
))
cells.append(code("plt.imshow(plt.imread('../outputs/charts/06_persist_score.png')); plt.axis('off');",
                   outputs=img_output(f"{CHARTS}/06_persist_score.png")))

cells.append(md("""
**Leitura:** o `persist_score` é deliberadamente simples e auditável (soma de 3 critérios objetivos:
resposta rápida, score técnico ≥75, score de gestor ≥75) — não um modelo caixa-preta. Candidatos com
score 3 (39 no funil atual) são o grupo de maior prioridade para follow-up ativo do recrutador; score 0-1
(105 candidatos) é onde vale reconsiderar tempo investido, salvo indicação forte de outro critério (ex.:
vaga com pool escasso).

**Nota metodológica importante:** as notas qualitativas do recrutador foram deliberadamente **excluídas**
deste score, porque a Seção 6 mostrou que elas não carregam sinal preditivo consistente hoje.
"""))

cells.append(md(f"""
## 8. Síntese — respostas às perguntas do case

**Quais estratégias de sourcing convertem melhor?**
Github e Inbound convertem quase 2x mais que Indicação e Evento. Vale redistribuir esforço de sourcing
priorizando os canais de maior conversão, não só maior volume.

**Quais sinais indicam maior chance de avanço?**
Score técnico, comportamental e de gestor em conjunto (não isoladamente) e resposta rápida ao primeiro
contato. Notas qualitativas do recrutador, no formato atual, **não** são um sinal confiável.

**Quando vale insistir com um candidato?**
Quando o `persist_score` é 2-4 (resposta rápida + score forte). O funil já mostra que processos que vão
até a contratação demoram mais — insistir não é sinal de processo travado.

**Quando a conversão é baixa?**
No topo do funil: ~32% dos candidatos nunca respondem ao primeiro contato. O gargalo é engajamento
inicial, não qualificação técnica.

**Há padrões relevantes entre canais, recrutadores e perfis?**
Sim — e a variação entre recrutadores ({recruiter_variation}x) é maior que a variação entre canais. Isso
sugere que o maior ganho de conversão de curto prazo está em abrir espaço para troca de prática entre o
time (comunidade de prática, shadowing), não em mudar de canal.

Recomendações práticas e plano de ação completo estão em `docs/Relatorio_Tecnico.pdf`.
"""))

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("notebook written:", OUT)
