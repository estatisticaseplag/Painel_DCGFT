# 👥 Dashboard RH – Dotação de Pessoal

Dashboard interativo para análise da base de dotação de pessoal, com filtros dinâmicos e exportação para Excel.

---

## 🚀 Como rodar (passo a passo)

### 1. Instale o Python
Baixe em: https://www.python.org/downloads/  
Versão recomendada: **Python 3.10 ou superior**

### 2. Instale as dependências
Abra o terminal (Prompt de Comando ou PowerShell) na pasta do projeto e rode:

```bash
pip install -r requirements.txt
```

### 3. Coloque o arquivo de dados na pasta
Certifique-se de que o arquivo **`BASE_DOTACAO.xlsx`** está na mesma pasta que `dashboard_rh.py`.

### 4. Inicie o dashboard
```bash
streamlit run dashboard_rh.py
```

O navegador abrirá automaticamente em: **http://localhost:8501**

---

## 📊 Funcionalidades

| Recurso | Descrição |
|---|---|
| 🔍 Filtros | Ano, Órgão, Situação Funcional, Situação Servidor, Remuneração Diferenciada |
| 📈 Gráficos | Evolução temporal, pizza situação funcional, top órgãos, top carreiras |
| 📋 Tabela | Dados agrupados e filtrados com scroll |
| ⬇️ Exportar | Botão para baixar os dados filtrados em **.xlsx** formatado |

---

## 📁 Estrutura dos arquivos

```
📂 pasta-do-projeto/
 ├── dashboard_rh.py       ← Aplicação principal
 ├── BASE_DOTACAO.xlsx     ← Base de dados
 ├── requirements.txt      ← Dependências Python
 └── README.md             ← Este arquivo
```

---

## 💡 Dicas de uso

- Use os filtros na **barra lateral esquerda** para refinar os dados
- O botão **"⬇️ Exportar Excel"** baixa exatamente os dados visíveis na tabela
- Deixe os filtros em branco para ver **todos os dados**
- Para atualizar a base, substitua o arquivo `BASE_DOTACAO.xlsx` e recarregue a página

---

*Desenvolvido com [Streamlit](https://streamlit.io) 🎈*
