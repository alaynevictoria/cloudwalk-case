"""
CloudWalk - Classificador de recruiter_notes via Claude (Anthropic API)
-----------------------------------------------------------------------
Este script é a versão "production-ready" da classificação de sinal
qualitativo usada em analysis.py. Ele NÃO precisa ser executado para
reproduzir o restante do projeto: o resultado já está cacheado em
outputs/ai_notes_classification.csv, exatamente como um pipeline real
faria cache de chamadas de LLM para não reprocessar o mesmo texto
duas vezes (custo, latência e reprodutibilidade).

Para rodar de fato, exporte sua chave e rode:
    export ANTHROPIC_API_KEY="sua-chave"
    python ai_note_classifier.py

O que ele faz:
1. Lê os templates únicos de recruiter_notes do dataset.
2. Envia cada um para o Claude com um prompt de classificação estruturada,
   pedindo tema e sinal (positivo / risco / misto) em JSON.
3. Salva o resultado em outputs/ai_notes_classification_live.csv.

Por que classificar por template e não linha a linha:
o dataset tem apenas 11 padrões de nota distintos entre 601 candidatos
(nota do recrutador é semi-estruturada, não texto livre único por pessoa).
Classificar os 11 templates é equivalente a classificar as 601 linhas,
mas evita 590 chamadas de API redundantes - a mesma lógica de cache
que se aplicaria a um volume real de notas de recrutador.
"""
import os
import json
import pandas as pd

CLASSIFICATION_PROMPT = """Você é um classificador de sinais qualitativos em processos seletivos.
Dada uma nota de recrutador sobre um(a) candidato(a), retorne APENAS um JSON com:
- "theme": um rótulo curto e específico do tema central da nota
- "signal": um entre "positive", "risk", "mixed"

Nota do recrutador: "{note}"

Responda apenas o JSON, sem texto adicional."""


def classify_note(client, note: str) -> dict:
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        messages=[{"role": "user", "content": CLASSIFICATION_PROMPT.format(note=note)}],
    )
    text = resp.content[0].text.strip()
    return json.loads(text)


def main():
    df = pd.read_csv("../data/mock_sourcing_dataset.csv")
    unique_notes = df.recruiter_notes.unique().tolist()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY não definido - pulando chamada real.")
        print(f"{len(unique_notes)} templates únicos seriam classificados:")
        for n in unique_notes:
            print(" -", n)
        return

    import anthropic
    client = anthropic.Anthropic()

    results = []
    for note in unique_notes:
        classification = classify_note(client, note)
        results.append({"recruiter_notes": note, **classification})
        print(note, "->", classification)

    pd.DataFrame(results).to_csv("../outputs/ai_notes_classification_live.csv", index=False)


if __name__ == "__main__":
    main()
