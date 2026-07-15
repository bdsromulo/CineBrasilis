"""Gera o QR Code do PIX (img/pix-qr.svg) a partir do payload copia e cola.

Um QR de PIX nao passa de uma string codificada: a mesma que o visitante
copia no botao "copia e cola". Por isso o SVG e derivado do PAYLOAD abaixo,
e nao de uma foto — o arquivo fica vetorial, leve e sempre em sincronia com
a string exibida na pagina.

Rode apenas quando o payload mudar:

    pip install segno
    python scripts/gerar_qr_pix.py

Requer: segno (apenas para gerar o arquivo; o site nao carrega biblioteca
nenhuma em tempo de execucao).
"""

import pathlib
import sys

import segno

# Payload copia e cola (padrao EMV do Banco Central). Publico por natureza:
# e exatamente o que qualquer pessoa le ao apontar a camera para o QR.
PAYLOAD = (
    "00020101021126580014br.gov.bcb.pix0136"
    "44a67e70-cbbd-4c38-b2de-1e4c5b4cb797"
    "5204000053039865802BR5917ROMULO B DA SILVA6008CURITIBA"
    "62070503***63046CD8"
)

DESTINO = pathlib.Path(__file__).resolve().parent.parent / "img" / "pix-qr.svg"


def crc16_ccitt(texto):
    """CRC-16/CCITT-FALSE — o checksum que o BCB exige no fim do payload."""
    crc = 0xFFFF
    for byte in texto.encode("utf-8"):
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def validar(payload):
    """Um digito trocado gera um QR que abre no banco e falha na hora de pagar.

    O proprio payload carrega seu checksum nos 4 ultimos digitos, entao da
    para detectar isso aqui, antes de gerar o arquivo.
    """
    if not payload[:-4].endswith("6304"):
        sys.exit("Payload invalido: nao ha campo CRC (6304) antes dos 4 ultimos digitos.")
    esperado = "%04X" % crc16_ccitt(payload[:-4])
    if esperado != payload[-4:].upper():
        sys.exit(f"CRC nao confere: payload traz {payload[-4:]}, calculado {esperado}.")


def main():
    validar(PAYLOAD)

    # error="m" (~15% de correcao) e o usado pelos bancos: sobra tolerancia a
    # arranhao e reflexo na tela sem inflar demais a malha do codigo.
    qr = segno.make(PAYLOAD, error="m")

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    # dark/light fixos: um QR precisa de modulos escuros sobre fundo claro para
    # ser lido, entao ele nao acompanha o tema do site (o painel poe uma placa
    # branca por tras justamente por isso).
    qr.save(
        DESTINO,
        kind="svg",
        scale=1,
        border=2,
        dark="#111111",
        light="#ffffff",
        svgclass=None,
        lineclass=None,
        omitsize=True,
    )

    print(f"Gerado: {DESTINO.relative_to(DESTINO.parent.parent)}")
    print(f"Versao do QR: {qr.version} | tamanho: {DESTINO.stat().st_size} bytes")


if __name__ == "__main__":
    main()
