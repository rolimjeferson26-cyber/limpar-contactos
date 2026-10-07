# Limpar Contactos → Lista limpa + relatório de alterações

Pega numa lista de contactos "suja" (CSV ou Excel) e devolve um Excel limpo, com cada alteração registada para poderes confirmar o que mudou.

> Todos os dados em `dados_exemplo/` são **fictícios**. Os emails usam o domínio `exemplo.pt` e os telefones começam por `90`, para não coincidirem com telemóveis reais.

## O que limpa

| Campo | Antes | Depois |
|---|---|---|
| Nome | `  MARIA   DA silva ` | `Maria da Silva` |
| Email | `  ANA@Exemplo.PT ` | `ana@exemplo.pt` (e valida o formato) |
| Telefone | `00351 900123456`, `(+351) 900-123-456` | `+351 900 123 456` |
| Data | `2025-03-05`, `5-3-2025`, `05.03.2025` | `05/03/2025` |
| Localidade | ` aveiro ` | `Aveiro` |
| Duplicados | mesmo email, escrito de formas diferentes | fica só o primeiro |

## O que o relatório contém

| Folha | Conteúdo |
|---|---|
| Resumo | Linhas lidas, contactos limpos, rejeitados, nº de alterações |
| Contactos | A lista limpa, com uma coluna de avisos (ex.: telefone estranho) |
| Rejeitados | Sem nome, email inválido ou duplicado, com o motivo |
| Alterações | Linha a linha: coluna, valor antes e valor depois |

## Instalação e uso

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |   Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

python gerar_dados_exemplo.py
python limpar_contactos.py --entrada dados_exemplo/contactos_sujos.csv --saida contactos_limpos.xlsx
```

Exemplo de saída:

```
Pronto! 66 lidas → 62 limpos, 4 rejeitados, 239 alterações registadas → contactos_limpos.xlsx
```

O ficheiro de entrada precisa das colunas `nome, email, telefone, data_registo, localidade`. Maiúsculas e minúsculas no cabeçalho não importam.

## Segurança e privacidade (RGPD)

- **Tudo local:** nada é enviado para a internet.
- **Nada de dados pessoais no ecrã:** só aparecem contagens.
- **O original nunca é alterado:** o script recusa gravar por cima do ficheiro de entrada.
- **Sem macros:** só aceita `.csv` e `.xlsx`. Os ficheiros `.xlsm` são recusados.
- **Injeção de fórmulas bloqueada:** um nome como `=1+1` fica guardado como texto.
- **Ficheiros grandes recusados:** acima de 20 MB, o ficheiro não é lido.
- **Dependências verificadas:** estão fixadas e foram auditadas com `pip-audit` (sem vulnerabilidades a 07/10/2026).
- **Com dados reais de clientes:** trabalha numa pasta `dados/`, que o `.gitignore` não deixa ir para o GitHub, e apaga tudo no fim do trabalho.

## Testes

```bash
python -m unittest -v
```

São 10 testes. Cobrem cada função de limpeza, duplicados, a garantia de que o original não muda, a saída por cima da entrada, fórmulas e extensões recusadas.

## Limitações conhecidas

- Os telefones são tratados como portugueses. Números estrangeiros ficam como estão, com um aviso.
- A validação de email apanha os erros comuns, mas não garante que o email existe.
- Uma data como `03/05/2025` é sempre lida como 3 de maio, porque o formato português põe o dia primeiro.
