# FinançasPro — Controle Financeiro Desktop

Aplicação desktop para Windows que organiza receitas e despesas por usuário, gera relatórios e mantém todos os dados localmente.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Tkinter](https://img.shields.io/badge/interface-Tkinter-0F766E)
![Status](https://img.shields.io/badge/status-projeto%20funcional-2563EB)

## Sobre o projeto

O FinançasPro demonstra a construção de uma aplicação desktop completa com interface gráfica, autenticação local, persistência em arquivos e geração de documentos. O foco é oferecer uma rotina financeira simples sem depender de servidor ou conexão com a internet.

## Funcionalidades

- Cadastro e login de usuários locais.
- Registro de receitas e despesas.
- Edição, exclusão e replicação de lançamentos.
- Repetição de uma movimentação por vários meses.
- Filtros por mês e ano.
- Resumo de receitas, despesas e saldo.
- Gráfico de despesas por categoria.
- Exportação mensal ou personalizada em PDF e CSV.
- Backup automático após alterações.
- Tema claro e escuro com preferência persistida.

## Decisões técnicas

- Interface construída com Tkinter e componentes `ttk`.
- Seleção de datas com `tkcalendar`.
- Persistência separada por usuário em arquivos CSV.
- Leitura e transformação de dados com pandas.
- Gráficos Matplotlib incorporados à janela.
- Relatórios PDF com ReportLab.
- Empacotamento para Windows com PyInstaller.

## Executando localmente

```bash
git clone https://github.com/vitorgoetmann/FinancasPRO.git
cd FinancasPRO
pip install tkcalendar matplotlib pandas reportlab
python controle_finanças.py
```

Para gerar o executável no Windows:

```bat
compilar.bat
```

## Estrutura dos dados

```text
usuarios/
├── usuario.cred.csv
├── usuario_receitas.csv
└── usuario_despesas.csv

config.json
```

Os dados e credenciais são locais. O projeto é adequado para estudo e uso pessoal; não deve ser tratado como uma solução de autenticação corporativa.

## Aprendizados demonstrados

- Desenvolvimento de interfaces desktop.
- Manipulação e persistência de dados tabulares.
- Visualização de dados e geração de documentos.
- Empacotamento de aplicações Python para Windows.

## Autor

Desenvolvido por [Vitor Goetmann](https://github.com/vitorgoetmann).
