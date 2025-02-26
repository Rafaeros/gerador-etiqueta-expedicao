# Gerador de Etiqueta de Expedição

![Badge](https://img.shields.io/badge/Python->=3.12-blue.svg) ![Badge](https://img.shields.io/badge/Status-Em%20desenvolvimento-yellow)

## 📌 Sobre o Projeto

O **Gerador de Etiqueta de Expedição** é uma aplicação desenvolvida em Python para a criação automatizada de etiquetas de expedição, facilitando o processo logístico e garantindo precisão nas informações impressas. 

## 🚀 Bibliotecas Utilizadas

- **PySide6** (para criação da interface)
- **PySerial** (para comunicação com balança)
- **AioHTTP** (para requisições assíncronas para coleta de dados)
- **BeautifulSoup** (para coleta de dados das requisições feitas pelo **AioHTTP**)
- **Json** (para gerar um relatório dos dados em formato json, para ser acessado pela aplicação)
- **ReportLab** (para geração de arquivos PDF com código de barras.)
- **PyWin32** (para manipulação de impressão nas impressoras Zebra)

## 📂 Estrutura do Projeto

```
📦 gerador-etiqueta-expedicao
 ┣ 📂 core
 ┃ ┣ 📂 assets
 ┃ ┣ 📜 balance_communication.py
 ┃ ┣ 📜 generate_labels.py
 ┃ ┣ 📜 get_data.py
 ┃ ┣ 📜 interface.py
 ┃ ┗ 📜 requests_api_go.py
 ┣ 📜 .gitignore
 ┣ 📜 main.py
 ┣ 📜 pyproject.toml
 ┗ 📜 README.md
```

## 📥 Instalação

1. Clone o repositório:
   ```sh
   git clone https://github.com/Rafaeros/gerador-etiqueta-expedicao.git
   ```
2. Acesse o diretório do projeto:
   ```sh
   cd gerador-etiqueta-expedicao
   ```
3. Instale o Python uv e acesse o ambiente virtual:
   ```sh
   uv sync
   Linux: source venv/bin/activate
   Windows: venv/Scripts/activate.ps1
   ```

## 🖨️ Como Usar

1. Execute o script principal:
   ```sh
   python main.py
   ```
2. Configure os parâmetros necessários para gerar as etiquetas.
3. As etiquetas geradas serão salvas no diretório especificado.

## 📜 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## ✨ Contribuição

Contribuições são bem-vindas! Para contribuir:
1. Fork este repositório
2. Crie uma branch (`git checkout -b feature/minha-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Faça push da sua branch (`git push origin feature/minha-feature`)
5. Abra um Pull Request

---

💡 Desenvolvido por [Rafaeros](https://github.com/Rafaeros)
