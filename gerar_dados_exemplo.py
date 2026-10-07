"""
Gera uma lista de contactos FICTÍCIOS e propositadamente "sujos"
em dados_exemplo/contactos_sujos.csv.

Os emails usam o domínio exemplo.pt e os telefones são inventados.

Uso:
    python gerar_dados_exemplo.py
"""

import csv
import random
from pathlib import Path

NOMES = ["Ana", "Rui", "Marta", "João", "Inês", "Pedro", "Sofia", "Tiago", "Carla", "Nuno"]
APELIDOS = ["Silva", "Santos", "Ferreira", "Oliveira", "Costa", "Rodrigues", "da Rocha", "dos Reis"]
LOCALIDADES = ["murtosa", "ESTARREJA", "Ovar", " aveiro ", "torreira", "ílhavo"]
PASTA = Path("dados_exemplo")


def sujar_telefone(numero: str) -> str:
    """Escreve o mesmo número de formas diferentes, como as pessoas fazem."""
    formas = [
        numero,
        f"{numero[:3]} {numero[3:6]} {numero[6:]}",
        f"+351{numero}",
        f"00351 {numero}",
        f"(+351) {numero[:3]}-{numero[3:6]}-{numero[6:]}",
    ]
    return random.choice(formas)


def sujar_data(dia: int, mes: int, ano: int) -> str:
    formas = [f"{dia:02d}/{mes:02d}/{ano}", f"{ano}-{mes:02d}-{dia:02d}",
              f"{dia}-{mes}-{ano}", f"{dia:02d}.{mes:02d}.{ano}"]
    return random.choice(formas)


def sujar_nome(nome: str) -> str:
    formas = [nome, nome.upper(), nome.lower(), "  " + nome.replace(" ", "   ") + " "]
    return random.choice(formas)


def gerar():
    random.seed(7)
    PASTA.mkdir(exist_ok=True)
    linhas = []

    for i in range(60):
        nome = f"{random.choice(NOMES)} {random.choice(APELIDOS)}"
        email_base = nome.lower().replace(" ", ".").replace("ã", "a").replace("ê", "e").replace("é", "e").replace("ó", "o")
        email = f"{email_base}{i}@exemplo.pt"
        if random.random() < 0.3:
            email = "  " + email.upper() + " "
        telefone = "90" + "".join(random.choices("0123456789", k=7))  # 90x: não é prefixo de telemóvel real
        linhas.append([
            sujar_nome(nome),
            email,
            sujar_telefone(telefone),
            sujar_data(random.randint(1, 28), random.randint(1, 12), random.choice([2024, 2025, 2026])),
            random.choice(LOCALIDADES),
        ])

    # Duplicados (mesmo email, escrito de forma diferente)
    linhas.append([linhas[0][0].upper(), linhas[0][1].strip().upper(), "", "", "Murtosa"])
    linhas.append([linhas[5][0], linhas[5][1], linhas[5][2], linhas[5][3], linhas[5][4]])

    # Erros de propósito
    linhas.append(["Rita Sousa", "rita.sousa@exemplo", "900123456", "01/01/2026", "Ovar"])   # email sem domínio
    linhas.append(["", "semnome@exemplo.pt", "", "", ""])                                   # nome em branco
    linhas.append(["Hugo Lima", "hugo.lima@exemplo.pt", "12345", "32/13/2025", "Ovar"])     # telefone e data maus (aviso)
    linhas.append(["=1+1", "formula@exemplo.pt", "", "", "@SUM(A1)"])                        # tentativa de fórmula

    random.shuffle(linhas)
    with open(PASTA / "contactos_sujos.csv", "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f, delimiter=";")
        escritor.writerow(["Nome", "Email", "Telefone", "Data_Registo", "Localidade"])
        escritor.writerows(linhas)
    print(f"Criado '{PASTA}/contactos_sujos.csv' com {len(linhas)} linhas")


if __name__ == "__main__":
    gerar()
