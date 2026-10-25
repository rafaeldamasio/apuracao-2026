"""Gera a imagem de prévia que aparece ao colar o link nas redes."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parent


def fonte(tamanho: int, negrito: bool = False) -> ImageFont.ImageFont:
    candidatos = [
        "C:/Windows/Fonts/segoeuib.ttf" if negrito else "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if negrito
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for caminho in candidatos:
        if Path(caminho).exists():
            return ImageFont.truetype(caminho, tamanho)
    return ImageFont.load_default()


def main() -> None:
    dados = json.loads((RAIZ / "dados.json").read_text(encoding="utf-8"))
    nacional = dados["nacional"]
    por_numero = {item["numero"]: item for item in nacional["candidatos"]}
    lula = por_numero.get("13", {"pct": "—", "nome": "Lula"})
    flavio = por_numero.get("22", {"pct": "—", "nome": "Flávio Bolsonaro"})

    imagem = Image.new("RGB", (1200, 630), "#0d0d0e")
    desenho = ImageDraw.Draw(imagem)
    desenho.rectangle((0, 0, 1200, 8), fill="#cc0000")
    desenho.text((72, 78), "Apuração presidencial 2026", font=fonte(42, True), fill="#ffffff")
    desenho.text((72, 138), "2º turno  ·  presidente", font=fonte(28), fill="#bdbdbd")
    desenho.text((72, 250), f"{lula['pct']}%", font=fonte(92, True), fill="#cc0000")
    desenho.text((72, 360), "Lula", font=fonte(36), fill="#ffffff")
    desenho.text((620, 250), f"{flavio['pct']}%", font=fonte(92, True), fill="#8fd9a8")
    desenho.text((620, 360), "Flávio Bolsonaro", font=fonte(36), fill="#ffffff")
    desenho.text(
        (72, 500),
        f"{nacional['pst']}% das seções apuradas  ·  atualizado em {dados['geradoEm']}  ·  Fonte: TSE",
        font=fonte(24),
        fill="#9a9a9a",
    )
    imagem.save(RAIZ / "og.png", "PNG")
    print("og.png atualizado")


if __name__ == "__main__":
    main()
