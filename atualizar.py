"""Busca a apuração presidencial no TSE e grava dados.json.

Só regrava o arquivo quando os números mudam. O horário gravado é o do
próprio TSE, então uma consulta sem novidade não altera o site.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import urllib.request
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
DESTINO = RAIZ / "dados.json"
ELEICAO = "6258"
CICLO = "ele2026"
BASE = f"https://resultados.tse.jus.br/oficial/{CICLO}/{ELEICAO}/dados"
FIM_AUTOMATICO = date(2026, 10, 28)

NOMES = {
    "ac": "Acre",
    "al": "Alagoas",
    "am": "Amazonas",
    "ap": "Amapá",
    "ba": "Bahia",
    "ce": "Ceará",
    "df": "Distrito Federal",
    "es": "Espírito Santo",
    "go": "Goiás",
    "ma": "Maranhão",
    "mg": "Minas Gerais",
    "ms": "Mato Grosso do Sul",
    "mt": "Mato Grosso",
    "pa": "Pará",
    "pb": "Paraíba",
    "pe": "Pernambuco",
    "pi": "Piauí",
    "pr": "Paraná",
    "rj": "Rio de Janeiro",
    "rn": "Rio Grande do Norte",
    "ro": "Rondônia",
    "rr": "Roraima",
    "rs": "Rio Grande do Sul",
    "sc": "Santa Catarina",
    "se": "Sergipe",
    "sp": "São Paulo",
    "to": "Tocantins",
}

ROTULOS = {"13": "Lula", "22": "Flávio Bolsonaro"}


def decodificar(texto: str) -> dict:
    carga = texto.strip().split(".")[1]
    carga += "=" * ((4 - len(carga) % 4) % 4)
    carga = carga.replace("-", "+").replace("_", "/")
    return json.loads(base64.b64decode(carga))


def baixar(url: str) -> dict:
    pedido = urllib.request.Request(
        url,
        headers={"User-Agent": "apuracao-2026", "Cache-Control": "no-cache"},
    )
    with urllib.request.urlopen(pedido, timeout=40) as resposta:
        return decodificar(resposta.read().decode("utf-8"))


def inteiro(valor) -> int:
    texto = str(valor or "0").replace(".", "")
    return int(texto.split(",")[0] or "0")


def candidatos_de(documento: dict) -> list[dict]:
    achados = []
    for cargo in documento.get("carg") or []:
        for grupo in cargo.get("agr") or []:
            for partido in grupo.get("par") or []:
                for candidato in partido.get("cand") or []:
                    achados.append(
                        {
                            "numero": str(candidato.get("n") or ""),
                            "nome": ROTULOS.get(str(candidato.get("n")), candidato.get("nmu") or ""),
                            "partido": partido.get("sg") or "",
                            "votos": inteiro(candidato.get("vap")),
                            "pct": candidato.get("pvap") or "0,00",
                        }
                    )
    achados.sort(key=lambda item: -item["votos"])
    return achados


def uf_de(sigla: str, acompanhamento: dict, nominal: dict) -> dict:
    votos = candidatos_de(nominal)
    total = sum(item["votos"] for item in votos)
    return {
        "uf": sigla.upper(),
        "nome": NOMES.get(sigla, "Exterior"),
        "pst": acompanhamento["s"]["pst"],
        "pstn": float(str(acompanhamento["s"]["pstn"]).replace(",", ".")),
        "st": inteiro(acompanhamento["s"]["st"]),
        "ts": inteiro(acompanhamento["s"]["ts"]),
        "comparecimento": inteiro(acompanhamento["e"]["c"]),
        "publicado": total > 0,
        "candidatos": votos if total > 0 else [],
    }


def montar() -> dict:
    brasil = baixar(f"{BASE}/br/br-c0001-e00{ELEICAO}-u.jws")
    acompanhamento = baixar(f"{BASE}/br/br-e00{ELEICAO}-ab.jws")
    por_uf = {item["cdabr"]: item for item in acompanhamento["abr"]}
    nominais = {}
    for sigla in [*NOMES, "zz"]:
        try:
            nominais[sigla] = baixar(f"{BASE}/{sigla}/{sigla}-c0001-e00{ELEICAO}-u.jws")
        except Exception as erro:
            print(f"aviso: {sigla} sem arquivo nominal ({erro})", file=sys.stderr)
            nominais[sigla] = {}

    votos_nacionais = candidatos_de(brasil)
    return {
        "geradoEm": f"{brasil.get('dt') or brasil.get('dg')} {brasil.get('ht') or brasil.get('hg')}".strip(),
        "eleicao": ELEICAO,
        "nacional": {
            "pst": brasil["s"]["pst"],
            "st": inteiro(brasil["s"]["st"]),
            "ts": inteiro(brasil["s"]["ts"]),
            "comparecimento": inteiro(brasil["e"]["c"]),
            "validos": inteiro(brasil["v"]["vv"]),
            "brancos": inteiro(brasil["v"]["vb"]),
            "nulos": inteiro(brasil["v"]["tvn"]),
            "pctBrancos": brasil["v"]["pvb"],
            "pctNulos": brasil["v"]["ptvn"],
            "candidatos": votos_nacionais,
        },
        "exterior": uf_de("zz", por_uf["zz"], nominais.get("zz") or {}),
        "ufs": [uf_de(sigla, por_uf[sigla], nominais.get(sigla) or {}) for sigla in NOMES],
    }


def main() -> int:
    forcar = os.environ.get("ATUALIZAR_FORCADO") == "1"
    if date.today() > FIM_AUTOMATICO and not forcar:
        print("Janela automática encerrada. Rode de novo com atualização manual se precisar.")
        return 0
    novo = montar()
    texto = json.dumps(novo, ensure_ascii=False, indent=2) + "\n"
    anterior = DESTINO.read_text(encoding="utf-8") if DESTINO.exists() else ""
    if texto == anterior:
        print("Sem mudança na apuração.")
        return 0
    DESTINO.write_text(texto, encoding="utf-8")
    print(f"dados.json atualizado: {novo['geradoEm']} · {novo['nacional']['pst']}% das seções")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
