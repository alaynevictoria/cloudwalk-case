# -*- coding: utf-8 -*-
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                 Image, HRFlowable, ListFlowable, ListItem)
from reportlab.lib.enums import TA_LEFT

NAVY = colors.HexColor("#101C33")
TEAL = colors.HexColor("#2E8B8B")
CORAL = colors.HexColor("#E07856")
GREY = colors.HexColor("#5B6472")
LINE = colors.HexColor("#E2E5EA")

CHARTS = "/home/claude/cloudwalk-sourcing-analysis/outputs/charts"
OUT = "/home/claude/cloudwalk-sourcing-analysis/docs/Relatorio_Tecnico.pdf"

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("H1", parent=styles["Heading1"], fontName="Helvetica-Bold",
                           fontSize=19, textColor=NAVY, spaceAfter=4))
styles.add(ParagraphStyle("H2", parent=styles["Heading2"], fontName="Helvetica-Bold",
                           fontSize=13, textColor=NAVY, spaceBefore=16, spaceAfter=6))
styles.add(ParagraphStyle("Body", parent=styles["Normal"], fontName="Helvetica",
                           fontSize=9.7, leading=14.5, textColor=colors.HexColor("#1E2733"),
                           alignment=TA_LEFT, spaceAfter=6))
styles.add(ParagraphStyle("Small", parent=styles["Normal"], fontName="Helvetica",
                           fontSize=8.3, leading=12, textColor=GREY))
styles.add(ParagraphStyle("Eyebrow", parent=styles["Normal"], fontName="Helvetica-Bold",
                           fontSize=8.5, textColor=TEAL, spaceAfter=2))
styles.add(ParagraphStyle("Insight", parent=styles["Body"], fontName="Helvetica",
                           fontSize=9.3, leading=13.5, textColor=NAVY,
                           backColor=colors.HexColor("#DCEDEC"), borderPadding=8,
                           spaceBefore=4, spaceAfter=10))

story = []

story.append(Paragraph("CLOUDWALK · CASE TÉCNICO — ATRAÇÃO E SELEÇÃO", styles["Eyebrow"]))
story.append(Paragraph("Análise do Funil de Sourcing", styles["H1"]))
story.append(Paragraph("Abordagem, decisões, uso de IA e principais insights", styles["Small"]))
story.append(Spacer(1, 6))
story.append(HRFlowable(width="100%", thickness=1, color=LINE))
story.append(Spacer(1, 10))

story.append(Paragraph(
    "Este documento resume a abordagem, as decisões tomadas e os principais insights da análise do "
    "funil de sourcing (601 candidatos, jan–jun/2025). A execução técnica completa está no notebook "
    "<b>sourcing_funnel_analysis.ipynb</b> e a demonstração interativa em <b>dashboard/index.html</b>.",
    styles["Body"]))

# ---------------- Abordagem ----------------
story.append(Paragraph("1. Abordagem", styles["H2"]))
story.append(Paragraph(
    "A análise foi estruturada em três camadas, na ordem em que um recrutador tomaria decisão:", styles["Body"]))
story.append(ListFlowable([
    ListItem(Paragraph("<b>Funil quantitativo</b> — onde e quanto se perde em cada etapa (sourcing → resposta → "
                        "screening → entrevista → teste → oferta → contratação).", styles["Body"])),
    ListItem(Paragraph("<b>Cortes de conversão</b> — canal, recrutador(a), senioridade, departamento e modalidade "
                        "de trabalho, para isolar onde a variação é estrutural (canal/vaga) e onde é de processo "
                        "(prática individual do recrutador).", styles["Body"])),
    ListItem(Paragraph("<b>Sinal qualitativo via IA</b> — testar se as notas do recrutador carregam informação "
                        "preditiva sobre contratação, em vez de assumir que carregam.", styles["Body"])),
], bulletType="bullet", start="•"))

# ---------------- Decisões ----------------
story.append(Paragraph("2. Decisões tomadas", styles["H2"]))
story.append(ListFlowable([
    ListItem(Paragraph("<b>Métrica central: taxa de contratação por grupo</b>, não taxa de avanço por etapa "
                        "isolada — evita otimizar uma etapa às custas do resultado final (contratação).", styles["Body"])),
    ListItem(Paragraph("<b>Persist Score como heurística explicável</b>, não modelo de ML caixa-preta: soma de 3 "
                        "critérios objetivos (resposta rápida, score técnico ≥75, score de gestor ≥75). Em um "
                        "processo real, um recrutador precisa conseguir explicar por que está priorizando alguém "
                        "— um score auditável serve esse propósito melhor que uma probabilidade de um modelo "
                        "estatístico sobre uma base de 601 linhas, que seria ruidosa e difícil de defender.", styles["Body"])),
    ListItem(Paragraph("<b>Notas do recrutador classificadas por template, não linha a linha</b>: o campo tem "
                        "apenas 11 padrões distintos entre 601 candidatos. Classificar os 11 templates evita "
                        "chamadas de API redundantes e é equivalente, em resultado, a classificar as 601 linhas.", styles["Body"])),
    ListItem(Paragraph("<b>Dados de recrutador apresentados sem ranking.</b> A variação de conversão entre "
                        "recrutadores é tratada como sinal de prática a compartilhar (lente de People/L&amp;D), "
                        "não como avaliação de desempenho individual — ver seção 4.", styles["Body"])),
    ListItem(Paragraph("<b>Cautela estatística explícita em cortes de baixo N.</b> Algumas comparações usam "
                        "amostras pequenas (ex.: um dos temas de nota tem apenas 1 candidato; comparações entre "
                        "recrutadores variam de 75 a 121 candidatos cada). Diferenças de poucos pontos percentuais "
                        "nesses cortes devem ser lidas como direção, não como certeza estatística.", styles["Body"])),
], bulletType="bullet", start="•"))

# ---------------- Uso de IA ----------------
story.append(Paragraph("3. Uso de IA", styles["H2"]))
story.append(Paragraph(
    "IA foi usada em dois momentos distintos do fluxo, com papéis diferentes:", styles["Body"]))
story.append(ListFlowable([
    ListItem(Paragraph("<b>Classificação estruturada de texto (Claude / Anthropic API)</b> — cada um dos 11 "
                        "templates de <font face='Courier'>recruiter_notes</font> foi classificado em tema e sinal "
                        "(positivo / risco / misto) via prompt estruturado com saída em JSON, simulando um "
                        "classificador de \"automated candidate feedback\" em produção. O código pronto para API "
                        "está em <font face='Courier'>notebooks/ai_note_classifier.py</font>; o resultado "
                        "cacheado está em <font face='Courier'>outputs/ai_notes_classification.csv</font>.", styles["Body"])),
    ListItem(Paragraph("<b>Apoio na construção da análise</b> — geração assistida de código de exploração de "
                        "dados, gráficos e do dashboard interativo, com toda a lógica de negócio, os cortes "
                        "escolhidos e a interpretação dos resultados definidos e revisados manualmente.", styles["Body"])),
], bulletType="bullet", start="•"))
story.append(Paragraph(
    "O ponto mais importante metodologicamente não é ter usado IA — é o que a classificação revelou: o sinal "
    "qualitativo, do jeito que está registrado hoje, <b>não prediz bem contratação</b> (seção 5). Reportar isso "
    "honestamente, em vez de forçar uma correlação, é o uso de IA que gera valor real para o time de recrutamento.",
    styles["Insight"]))

# ---------------- Insights ----------------
story.append(Paragraph("4. Principais insights", styles["H2"]))

data = [
    ["Etapa", "Sourced", "Respondeu", "Screening", "Entrevista", "Teste", "Oferta", "Contratado"],
    ["Candidatos", "601", "408", "308", "234", "201", "62", "49"],
    ["% do total", "100%", "68%", "51%", "39%", "33%", "10%", "8,2%"],
]
t = Table(data, colWidths=[26*mm]+[19.5*mm]*7)
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
    ("FONTSIZE", (0, 0), (-1, -1), 7.6),
    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F6F8")]),
    ("GRID", (0, 0), (-1, -1), 0.5, LINE),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
]))
story.append(t)
story.append(Spacer(1, 8))

insights = [
    ("Maior perda é engajamento, não qualificação.",
     "32% dos candidatos sourced nunca respondem ao primeiro contato — o maior degrau de todo o funil, "
     "e ele acontece antes de qualquer avaliação técnica."),
    ("A variação entre recrutadores é maior que entre canais.",
     "A diferença entre a maior e a menor taxa de conversão do time (volume comparável, ~100 candidatos "
     "cada) é maior que a diferença entre o melhor e o pior canal. Isso costuma indicar prática valiosa "
     "concentrada em parte do time e ainda não compartilhada — um sinal para comunidade de prática ou "
     "shadowing, não uma métrica de avaliação individual."),
    ("Os três scores pesam — não só o técnico.",
     "Contratados pontuam mais alto em técnico, comportamental e gestor (gap de ~7-9 pontos nos três). "
     "Filtrar só pela nota técnica descarta sinal relevante."),
    ("Contratados passam ~3,5x mais tempo no funil (32 vs. 9 dias).",
     "Processos rejeitados terminam rápido; processos que viram contratação demoram mais. Fechar um "
     "candidato como \"sem fit\" cedo demais pode estar cortando processo antes do tempo natural."),
    ("O sinal qualitativo da nota do recrutador tem baixo poder preditivo.",
     "Classificado por IA em positivo/risco/misto, o sinal não separa bem quem é contratado (risco 8,0% "
     "vs. positivo 7,4% — diferença dentro do ruído). \"Misto\" (atrito salarial) converte mais (14,0%), "
     "sugerindo que objeção de salário não deveria ser motivo de descarte automático."),
]
for title, body in insights:
    story.append(Paragraph(f"<b>• {title}</b>", styles["Body"]))
    story.append(Paragraph(body, styles["Body"]))
    story.append(Spacer(1, 2))

story.append(Spacer(1, 6))
story.append(Image(f"{CHARTS}/03_recrutador.png", width=82*mm, height=52*mm))
story.append(Spacer(1, 4))
story.append(Paragraph("Conversão por recrutador(a), em ordem alfabética — a variação existe, mas o gráfico não ranqueia.", styles["Small"]))

# ---------------- Recomendações ----------------
story.append(Paragraph("5. Recomendações práticas", styles["H2"]))
story.append(ListFlowable([
    ListItem(Paragraph("Redistribuir esforço de sourcing priorizando canais de maior conversão (Github, Inbound), "
                        "não apenas maior volume (Comunidade, Evento).", styles["Body"])),
    ListItem(Paragraph("Criar rodadas de compartilhamento de prática entre recrutadores(as) — a variação de "
                        "conversão no time é maior que a variação entre canais, sinal de prática rica pra "
                        "trocar. Formato sugerido: shadowing em pares ou comunidade de prática mensal.", styles["Body"])),
    ListItem(Paragraph("Testar cadência de follow-up nos primeiros 3 dias para reduzir os 32% de \"sem resposta\" "
                        "no topo do funil.", styles["Body"])),
    ListItem(Paragraph("Até padronizar o registro de notas qualitativas, priorizar candidatos ativos por score "
                        "objetivo + velocidade de resposta (Persist Score), não por impressão geral do recrutador.", styles["Body"])),
], bulletType="bullet", start="•"))

story.append(Spacer(1, 14))
story.append(HRFlowable(width="100%", thickness=0.6, color=LINE))
story.append(Spacer(1, 6))
story.append(Paragraph(
    "Repositório completo: notebook, dashboard interativo e dados em anexo. Dataset fictício fornecido pela CloudWalk.",
    styles["Small"]))

doc = SimpleDocTemplate(OUT, pagesize=A4,
                         leftMargin=20*mm, rightMargin=20*mm, topMargin=16*mm, bottomMargin=16*mm)
doc.build(story)
print("PDF written:", OUT)
