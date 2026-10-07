"""
limpar_contactos.py
-------------------
Limpa uma lista de contactos "suja" (CSV ou Excel):
  - tira espaços a mais e põe os nomes com maiúsculas certas
  - normaliza telefones portugueses para o formato +351 9XX XXX XXX
  - converte datas em vários formatos para DD/MM/AAAA
  - valida emails e remove duplicados (pelo email)
  - regista TODAS as alterações num relatório, para o cliente confiar no resultado

Uso:
    python limpar_contactos.py --entrada dados_exemplo/contactos_sujos.csv --saida contactos_limpos.xlsx

Segurança e privacidade:
  - Trabalha só no teu computador; não envia nada para a internet.
  - No ecrã só mostra contagens, nunca nomes, emails ou telefones.
  - Nunca altera o ficheiro original: cria sempre um ficheiro novo.
  - Protege o Excel contra injeção de fórmulas (=, +, -, @).
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

COLUNAS = ["nome", "email", "telefone", "data_registo", "localidade"]
TAMANHO_MAXIMO_MB = 20
CARACTERES_PERIGOSOS = ("=", "+", "-", "@", "\t", "\r")

# Formatos de data aceites, por ordem. Em Portugal o dia vem primeiro.
FORMATOS_DATA = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d.%m.%Y"]

# Validação simples de email: algo@algo.algo, sem espaços.
# (Não apanha 100% dos casos estranhos, mas apanha os erros comuns.)
PADRAO_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$")

# Palavras que ficam em minúsculas nos nomes portugueses
PARTICULAS = {"da", "de", "do", "das", "dos", "e"}


# ----------------------------------------------------------------------
# Funções de limpeza: cada uma recebe UM valor e devolve (valor_limpo, problema)
# problema = "" quando está tudo bem
# ----------------------------------------------------------------------
def limpar_nome(valor: str) -> tuple[str, str]:
    partes = valor.split()  # split() sem argumentos também remove espaços duplos
    if not partes:
        return "", "nome em branco"
    palavras = [p.lower() if p.lower() in PARTICULAS else p.capitalize() for p in partes]
    palavras[0] = palavras[0].capitalize()  # a primeira palavra é sempre maiúscula
    return " ".join(palavras), ""


def limpar_email(valor: str) -> tuple[str, str]:
    email = valor.strip().lower()
    if not email:
        return "", "email em branco"
    if not PADRAO_EMAIL.match(email):
        return email, "email inválido"
    return email, ""


def limpar_telefone(valor: str) -> tuple[str, str]:
    """Aceita 912345678, 912 345 678, +351912345678, 00351 912..., (+351) 912-345-678."""
    if not valor.strip():
        return "", ""  # telefone é opcional
    digitos = re.sub(r"\D", "", valor)  # fica só com os números
    if digitos.startswith("00351"):
        digitos = digitos[5:]
    elif digitos.startswith("351") and len(digitos) == 12:
        digitos = digitos[3:]
    # Números portugueses têm 9 dígitos e começam por 9 (móvel) ou 2 (fixo)
    if len(digitos) != 9 or digitos[0] not in "29":
        return valor.strip(), "telefone não parece português"
    return f"+351 {digitos[:3]} {digitos[3:6]} {digitos[6:]}", ""


def limpar_data(valor: str) -> tuple[str, str]:
    texto = valor.strip()
    if not texto:
        return "", ""  # data é opcional
    for formato in FORMATOS_DATA:
        try:
            data = datetime.strptime(texto, formato)
        except ValueError:
            continue
        if data > datetime.now():
            return texto, "data no futuro"
        return data.strftime("%d/%m/%Y"), ""
    return texto, "data em formato desconhecido"


def limpar_localidade(valor: str) -> tuple[str, str]:
    return limpar_nome(valor)[0], ""  # mesma regra de maiúsculas, sem erro se vazio


LIMPEZAS = {
    "nome": limpar_nome,
    "email": limpar_email,
    "telefone": limpar_telefone,
    "data_registo": limpar_data,
    "localidade": limpar_localidade,
}


# ----------------------------------------------------------------------
# Leitura
# ----------------------------------------------------------------------
def ler_entrada(caminho: Path) -> pd.DataFrame:
    if not caminho.is_file() or caminho.is_symlink():
        raise FileNotFoundError(f"O ficheiro '{caminho}' não existe.")
    if caminho.stat().st_size / (1024 * 1024) > TAMANHO_MAXIMO_MB:
        raise ValueError(f"O ficheiro tem mais de {TAMANHO_MAXIMO_MB} MB.")

    extensao = caminho.suffix.lower()
    if extensao == ".csv":
        df = pd.read_csv(caminho, sep=None, engine="python", dtype=str,
                         encoding="utf-8-sig", keep_default_na=False)
    elif extensao == ".xlsx":
        # .xlsx não corre macros; ficheiros .xlsm (com macros) são recusados de propósito
        df = pd.read_excel(caminho, dtype=str, keep_default_na=False)
    else:
        raise ValueError("Só aceito ficheiros .csv ou .xlsx")

    df.columns = [str(c).strip().lower() for c in df.columns]
    em_falta = [c for c in COLUNAS if c not in df.columns]
    if em_falta:
        raise ValueError(f"Faltam as colunas: {', '.join(em_falta)}")
    df = df[COLUNAS].copy()
    df.insert(0, "linha_origem", range(2, len(df) + 2))
    return df


# ----------------------------------------------------------------------
# Limpeza da tabela inteira
# ----------------------------------------------------------------------
def limpar_tabela(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Devolve (limpos, rejeitados, alteracoes)."""
    limpos, rejeitados, alteracoes = [], [], []

    for _, linha in df.iterrows():
        nova = {"linha_origem": linha["linha_origem"]}
        problemas = []
        for coluna, funcao in LIMPEZAS.items():
            original = str(linha[coluna])
            limpo, problema = funcao(original)
            nova[coluna] = limpo
            if problema:
                problemas.append(f"{coluna}: {problema}")
            if limpo != original:
                alteracoes.append({"linha_origem": linha["linha_origem"], "coluna": coluna,
                                   "antes": original, "depois": limpo})

        # Só rejeitamos quando falta o essencial: nome ou email válidos.
        # Telefone/data com problema ficam, mas com aviso.
        criticos = [p for p in problemas if p.startswith(("nome", "email"))]
        if criticos:
            rejeitados.append({**nova, "motivo": "; ".join(problemas)})
        else:
            nova["avisos"] = "; ".join(problemas)
            limpos.append(nova)

    limpos_df = pd.DataFrame(limpos, columns=["linha_origem", *COLUNAS, "avisos"])
    rejeitados_df = pd.DataFrame(rejeitados, columns=["linha_origem", *COLUNAS, "motivo"])
    alteracoes_df = pd.DataFrame(alteracoes, columns=["linha_origem", "coluna", "antes", "depois"])

    # Duplicados: mesmo email. Fica a PRIMEIRA ocorrência, as outras vão para rejeitados.
    duplicado = limpos_df.duplicated(subset="email", keep="first")
    if duplicado.any():
        dups = limpos_df[duplicado].drop(columns="avisos").assign(motivo="email duplicado")
        rejeitados_df = pd.concat([rejeitados_df, dups], ignore_index=True)
        limpos_df = limpos_df[~duplicado]

    return limpos_df.reset_index(drop=True), rejeitados_df, alteracoes_df


# ----------------------------------------------------------------------
# Escrita segura
# ----------------------------------------------------------------------
TELEFONE_LIMPO = re.compile(r"^\+351 \d{3} \d{3} \d{3}$")


def proteger_texto(valor):
    """Põe um apóstrofo antes de texto que o Excel possa tratar como fórmula.
    Exceção: telefones que NÓS próprios formatámos (+351 ...) são seguros."""
    if isinstance(valor, str) and TELEFONE_LIMPO.match(valor):
        return valor
    if isinstance(valor, str) and valor.startswith(CARACTERES_PERIGOSOS):
        return "'" + valor
    return valor


def escrever_excel(caminho: Path, folhas: dict[str, pd.DataFrame]) -> None:
    with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
        for nome, tabela in folhas.items():
            tabela = tabela.copy()
            for coluna in tabela.columns:
                if tabela[coluna].dtype == object or pd.api.types.is_string_dtype(tabela[coluna]):
                    tabela[coluna] = tabela[coluna].map(proteger_texto)
            tabela.to_excel(writer, sheet_name=nome, index=False)
            folha = writer.sheets[nome]
            for col in folha.columns:
                largura = max(len(str(c.value or "")) for c in col) + 2
                folha.column_dimensions[col[0].column_letter].width = min(largura, 45)
            folha.freeze_panes = "A2"


def limpar_contactos(entrada: Path, saida: Path) -> dict:
    if entrada.resolve() == saida.resolve():
        raise ValueError("A saída não pode ser o próprio ficheiro de entrada.")
    df = ler_entrada(entrada)
    limpos, rejeitados, alteracoes = limpar_tabela(df)

    resumo = pd.DataFrame({
        "indicador": ["Linhas lidas", "Contactos limpos", "Rejeitados", "Alterações feitas"],
        "valor": [len(df), len(limpos), len(rejeitados), len(alteracoes)],
    })
    escrever_excel(saida, {"Resumo": resumo, "Contactos": limpos,
                           "Rejeitados": rejeitados, "Alterações": alteracoes})
    return {"lidas": len(df), "limpos": len(limpos),
            "rejeitados": len(rejeitados), "alteracoes": len(alteracoes)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Limpa uma lista de contactos.")
    parser.add_argument("--entrada", required=True, help="Ficheiro .csv ou .xlsx")
    parser.add_argument("--saida", default="contactos_limpos.xlsx", help="Ficheiro .xlsx a criar")
    args = parser.parse_args()

    saida = Path(args.saida)
    if saida.suffix.lower() != ".xlsx":
        print("ERRO: a saída tem de terminar em .xlsx")
        return 1
    try:
        r = limpar_contactos(Path(args.entrada), saida)
    except (FileNotFoundError, ValueError) as erro:
        print(f"ERRO: {erro}")
        return 1
    except PermissionError:
        print(f"ERRO: não consigo escrever '{saida}'. Está aberto no Excel?")
        return 1

    # Só contagens no ecrã: nada de dados pessoais
    print(f"Pronto! {r['lidas']} lidas → {r['limpos']} limpos, {r['rejeitados']} rejeitados, "
          f"{r['alteracoes']} alterações registadas → {saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
