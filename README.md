# Automação para Alterações de Preços do Comercial no Visual Store WEB:

Este projeto é uma ferramenta de automação desenvolvida em Python para processar planilhas de catálogo de produtos. O sistema lê descrições de produtos e preços de venda, adaptando os dados para uso na automação.

## 🎯 Objetivo
O principal objetivo é automatizar a criação ou alteração de preços de várias categorias utilizadas na plataforma do Visual Store (Sistema que gerencia PDV's)

## ⚙️ Funcionalidades

- **Leitura de Planilhas:** Processamento eficiente de arquivos Excel (`.xlsx`) utilizando as bibliotecas `openpyxl e Pandas`.
- **Log de alterações:** Output dos dados alterados no terminal.
- **Sanitização de Dados:** Trata inconsistências comuns em planilhas (vírgulas vs pontos) e preserva zeros à esquerda em Códigos de Barras.

## 🛠️ Tecnologias Utilizadas

- **Python 3.12+**
- **Pandas:** Manipulação e análise de dados.
- **OpenPyXL:** Leitura e escrita de arquivos Excel.
- **Selenium/Webdriver-Manager:** Automação de Browser.


## 📝 Autor

Desenvolvido por **Marlon Macedo**.  
Projeto criado para otimização de processos de Operacionais.
