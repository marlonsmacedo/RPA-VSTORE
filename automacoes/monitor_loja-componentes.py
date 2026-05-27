import os
import time, json
from typing import List

from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from drivers.driver import get_driver


def processar():

    usuario: str = os.environ["VSTORE_USER"]
    senha: str = os.environ["VSTORE_PASSWORD"]
    url: str = os.environ["VSTORE_URL"]
    monitor_url: str = os.environ["VSTORE_MONITOR_URL"]
    driver, driver_options = get_driver()
    driver_options.headless = True
    driver.get(url)
    driver.find_element(By.XPATH, "//input[@id='usuarios']").send_keys(usuario)
    driver.find_element(By.XPATH, "//input[@id='senha']").send_keys(senha)
    driver.find_element(By.XPATH, "//input[@id='btnEnviar']").click()

    time.sleep(1)

    driver.get(monitor_url)

    select_lista_lojas = Select(WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//select[@name='cmbLoja']"))))
    options_text = [option.text for option in select_lista_lojas.options]

    data = {}


    for option_text in options_text[1:]:

        select_lista_lojas.select_by_visible_text(option_text)
        select_lista_lojas = Select(WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//select[@name='cmbLoja']"))))


        # ---- Passo 1: Acessar o elemento que contem a tebela com os dados dos componentes ----
        lista = driver.find_elements(By.XPATH, "//table[@class='Lista']/tbody/tr")
        # lista[0] é o cabeçalho da tabela com o nome das das colunas.
        # lista[1] são dos dados das cargas da loja geradas no servidor.
        # lista[3] é vazia.
        # ---- Passo 2: montar json com dados das cargas do servidor e componentes ----
        loja: str = lista[1].find_elements(By.CLASS_NAME, "ListaLinha1")[2].text
        ultima_comunicacao = lista[1].find_elements(By.CLASS_NAME, "ListaLinha1")[5].text
        ultima_carga_produtos = lista[1].find_elements(By.CLASS_NAME, "ListaLinha1")[7].text
        ultima_carga_parametros = lista[1].find_elements(By.CLASS_NAME, "ListaLinha1")[9].text
        ultima_carga_pictures = lista[1].find_elements(By.CLASS_NAME, "ListaLinha1")[11].text
        ultima_carga_clientes = lista[1].find_elements(By.CLASS_NAME, "ListaLinha1")[12].text

        data[f"Filial: {loja}"] = {
            "Carga Servidor":
                {
                    "ultima_comunicacao": ultima_comunicacao,
                    "Data produtos": ultima_carga_produtos,
                    "Carga parametros": ultima_carga_parametros,
                    "Carga pictures": ultima_carga_pictures,
                    "Carga clientes": ultima_carga_clientes
                },
        }

        lista_componentes = []
        # ---- Iterar dados dos componentes ----
        for item in lista[3:-1]:
            componente = f"{item.find_elements(By.TAG_NAME, "td")[1].text}"
            localizacao = item.find_elements(By.TAG_NAME, "td")[4].text
            tipo_status = item.find_elements(By.TAG_NAME, "td")[2].text
            tipo, status = tipo_status.split(" ") if tipo_status != "PDV (Fechado Parcial)" else ("PDV", "(Fechado Parcial)")
            ultima_comunicacao = item.find_elements(By.TAG_NAME, "td")[5].text
            produtos = item.find_elements(By.TAG_NAME, "td")[7].text
            parametros = item.find_elements(By.TAG_NAME, "td")[9].text
            pictures = item.find_elements(By.TAG_NAME, "td")[11].text
            clientes = item.find_elements(By.TAG_NAME, "td")[12].text
            # print(componente, tipo, status, ultima_comunicacao, produtos, parametros, pictures, clientes)

            lista_componentes.append({
                f"PDV {componente}": {
                    "tipo": tipo,
                    "status": status,
                    "localização": localizacao,
                    "ultima_comunicacao": ultima_comunicacao,
                    "produtos": produtos,
                    "parametros": parametros,
                    "pictures": pictures,
                    "clientes": clientes
                }
            })
        data[f"Filial: {loja}"].update({"componentes" : lista_componentes})

    with open("dados.json", "w", encoding="utf-8") as file:
        file.write(json.dumps(data, indent=2, ensure_ascii=False))




import json
from collections import OrderedDict
from html import escape

def carregar_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def extrair_lista_componentes(filial_info):
    """
    Retorna a lista de componentes pertencentes àquela filial.
    Trata variações: chave 'componentes' / 'Componentes' ou primeira lista plausível.
    """
    if isinstance(filial_info, dict):
        for key in ("componentes", "Componentes"):
            val = filial_info.get(key)
            if isinstance(val, list):
                return val
        # procurar a primeira lista de dicionários plausível dentro do dict
        for v in filial_info.values():
            if isinstance(v, list) and all(isinstance(i, dict) for i in v):
                return v
        return []
    if isinstance(filial_info, list):
        return filial_info
    return []

def deduplicar_por_nome(componentes):
    """
    Recebe lista de componentes (cada item é dict com 1 chave: nome -> detalhes)
    Retorna OrderedDict nome -> detalhes, mantendo a última ocorrência por padrão.
    """
    mapa = OrderedDict()
    for comp in componentes:
        if not isinstance(comp, dict):
            continue
        for nome, detalhes in comp.items():
            mapa[nome.strip()] = detalhes
    return mapa

def filtrar_offline_por_filial(dados):
    """
    Retorna dict { filial_nome: [ (nome, detalhes), ... ] } contendo apenas
    os componentes daquela filial cujo status == "(Off-Line)".
    """
    resultado = {}
    top = dados.get("data") if isinstance(dados, dict) and "data" in dados else dados

    if not isinstance(top, dict):
        return resultado

    for filial_nome, filial_info in top.items():
        componentes_lista = extrair_lista_componentes(filial_info)
        mapa = deduplicar_por_nome(componentes_lista)

        offline = []
        for nome, detalhes in mapa.items():
            if not isinstance(detalhes, dict):
                continue
            status = (detalhes.get("status") or detalhes.get("Status") or "").strip()
            tipo = detalhes.get("tipo")
            if status == "(Off-Line)" and (tipo == "Totem" or tipo == "PDV" or tipo == "Mata-Burro"):
                offline.append((nome, detalhes))
        if offline:
            resultado[filial_nome] = offline

    return resultado


def gerar_html_relatorio(offline_dict, titulo="Relatório de Componentes Off-Line"):

    from html import escape

    total = sum(len(v) for v in offline_dict.values())

    html = [
        "<!DOCTYPE html>",
        "<html lang='pt-BR'>",

        "<head>",
        "  <meta charset='utf-8'>",
        "  <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
        f"  <title>{escape(titulo)}</title>",

        "  <style>",

        "    *{",
        "       box-sizing:border-box;",
        "    }",

        "    body{",
        "       margin:0;",
        "       padding:30px;",
        "       background:#f4f6f9;",
        "       font-family:Segoe UI, Arial, sans-serif;",
        "       color:#2d3436;",
        "    }",

        "    .container{",
        "       max-width:1400px;",
        "       margin:auto;",
        "    }",

        "    .header{",
        "       background:white;",
        "       border-radius:18px;",
        "       padding:28px 36px;",
        "       box-shadow:0 4px 14px rgba(0,0,0,0.08);",
        "       display:flex;",
        "       align-items:center;",
        "       gap:28px;",
        "       margin-bottom:30px;",
        "       min-height:140px;",
        "    }",

        "    .header img{",
        "       width:96px;",
        "       height:96px;",
        "       border-radius:50%;",
        "       object-fit:cover;",
        "       border:4px solid #e74c3c;",
        "       flex-shrink:0;",
        "    }",

        "    .header-content{",
        "       flex:1;",
        "    }",

        "    .header-content h1{",
        "       margin:0 0 10px 0;",
        "       font-size:34px;",
        "       line-height:1.2;",
        "       color:#2c3e50;",
        "       font-weight:700;",
        "    }",

        "    .header-content p{",
        "       margin:0;",
        "       color:#636e72;",
        "       font-size:15px;",
        "       line-height:1.6;",
        "    }",

        "    .summary{",
        "       margin-top:18px;",
        "       display:inline-flex;",
        "       align-items:center;",
        "       background:#e74c3c;",
        "       color:white;",
        "       padding:10px 18px;",
        "       border-radius:999px;",
        "       font-weight:bold;",
        "       font-size:15px;",
        "       box-shadow:0 3px 8px rgba(231,76,60,0.25);",
        "    }",

        "    .filial-card{",
        "       background:white;",
        "       border-radius:16px;",
        "       padding:22px;",
        "       margin-bottom:24px;",
        "       box-shadow:0 4px 10px rgba(0,0,0,0.06);",
        "    }",

        "    .filial-title{",
        "       margin:0 0 18px 0;",
        "       color:#2c3e50;",
        "       font-size:22px;",
        "       border-left:6px solid #e74c3c;",
        "       padding-left:12px;",
        "    }",

        "    table{",
        "       width:100%;",
        "       border-collapse:collapse;",
        "       overflow:hidden;",
        "       border-radius:12px;",
        "    }",

        "    thead{",
        "       background:#2c3e50;",
        "       color:white;",
        "    }",

        "    th{",
        "       padding:14px;",
        "       text-align:left;",
        "       font-size:14px;",
        "       font-weight:600;",
        "    }",

        "    td{",
        "       padding:14px;",
        "       border-bottom:1px solid #ecf0f1;",
        "       font-size:14px;",
        "       vertical-align:middle;",
        "    }",

        "    tbody tr:nth-child(even){",
        "       background:#fafafa;",
        "    }",

        "    tbody tr:hover{",
        "       background:#fceaea;",
        "       transition:0.2s;",
        "    }",

        "    .offline-badge{",
        "       display:inline-block;",
        "       background:#e74c3c;",
        "       color:white;",
        "       padding:6px 12px;",
        "       border-radius:999px;",
        "       font-size:12px;",
        "       font-weight:bold;",
        "       letter-spacing:0.3px;",
        "    }",

        "    .empty{",
        "       background:white;",
        "       padding:40px;",
        "       border-radius:16px;",
        "       text-align:center;",
        "       box-shadow:0 4px 12px rgba(0,0,0,0.06);",
        "       color:#636e72;",
        "       font-size:18px;",
        "    }",

        "    .footer{",
        "       margin-top:30px;",
        "       text-align:center;",
        "       color:#95a5a6;",
        "       font-size:13px;",
        "    }",

        "    @media(max-width:900px){",

        "       body{",
        "           padding:12px;",
        "       }",

        "       .header{",
        "           flex-direction:column;",
        "           text-align:center;",
        "           padding:24px;",
        "       }",

        "       .header-content h1{",
        "           font-size:28px;",
        "       }",

        "       table{",
        "           display:block;",
        "           overflow-x:auto;",
        "       }",

        "    }",

        "  </style>",
        "</head>",

        "<body>",

        "  <div class='container'>",

        "    <div class='header'>",

        "       <img src='https://media.giphy.com/avatars/superprix/qrme2AlWQ43C/200h.jpg'>",

        "       <div class='header-content'>",

        f"          <h1>{escape(titulo)}</h1>",

        "          <p>",
        "             Monitoramento automático dos componentes PDV com status OFF-LINE ",
        "             identificados no ambiente VisualMix.",
        "          </p>",

        f"          <div class='summary'>",
        f"              🔴 {total} componente(s) OFF-LINE detectado(s)",
        "          </div>",

        "       </div>",

        "    </div>"
    ]

    if not offline_dict:

        html.extend([
            "    <div class='empty'>",
            "       Nenhum componente <strong>OFF-LINE</strong> encontrado.",
            "    </div>"
        ])

    else:

        for filial, comps in offline_dict.items():

            html.extend([

                "    <div class='filial-card'>",

                f"      <h2 class='filial-title'>{escape(filial)} ({len(comps)} OFF-LINE)</h2>",

                "      <table>",

                "         <thead>",
                "             <tr>",
                "                 <th>Componente</th>",
                "                 <th>Tipo</th>",
                "                 <th>Status</th>",
                "                 <th>Localização</th>",
                "                 <th>Última Comunicação</th>",
                "             </tr>",
                "         </thead>",

                "         <tbody>"
            ])

            for nome, detalhes in comps:

                tipo = escape(str(detalhes.get("tipo", "")))
                status = escape(str(detalhes.get("status", "")))
                local = escape(str(detalhes.get("localização", "")))
                ultima = escape(str(detalhes.get("ultima_comunicacao", "")))

                html.extend([

                    "             <tr>",

                    f"                 <td><strong>{escape(nome)}</strong></td>",
                    f"                 <td>{tipo}</td>",
                    f"                 <td><span class='offline-badge'>{status}</span></td>",
                    f"                 <td>{local}</td>",
                    f"                 <td>{ultima}</td>",

                    "             </tr>"
                ])

            html.extend([

                "         </tbody>",
                "      </table>",
                "    </div>"
            ])

    html.extend([

        "    <div class='footer'>",
        "       Relatório gerado automaticamente pelo monitoramento VisualMix PDV",
        "    </div>",

        "  </div>",

        "</body>",
        "</html>"
    ])

    return '\n'.join(html)


import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def enviar_email_html():

    smtp_server = os.environ["VSTORE_SMTP_SERVER"]
    smtp_port = int(os.environ.get("VSTORE_SMTP_PORT", "25"))

    remetente = os.environ["VSTORE_EMAIL_FROM"]
    destinatario = os.environ["VSTORE_EMAIL_TO"]

    assunto = "Relatório de Componentes OFF-LINE"

    with open("offline_componentes.html", "r", encoding="utf-8") as file:
        html_content = file.read()

    mensagem = MIMEMultipart("alternative")

    mensagem["Subject"] = assunto
    mensagem["From"] = remetente
    mensagem["To"] = destinatario

    parte_html = MIMEText(html_content, "html", "utf-8")

    mensagem.attach(parte_html)

    try:

        servidor = smtplib.SMTP(smtp_server, smtp_port)

        servidor.ehlo()

        # Caso o servidor aceite TLS
        try:
            servidor.starttls()
            servidor.ehlo()
        except:
            pass

        servidor.sendmail(
            remetente,
            destinatario,
            mensagem.as_string()
        )

        servidor.quit()

        print("E-mail enviado com sucesso!")

    except Exception as erro:
        print(f"Erro ao enviar e-mail: {erro}")



if __name__ == "__main__":
    processar()
    dados = carregar_json("dados.json")          # substitua pelo seu arquivo
    offline_por_filial = filtrar_offline_por_filial(dados)
    html = gerar_html_relatorio(offline_por_filial)
    with open("offline_componentes.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Relatório gerado: offline_componentes.html")
    enviar_email_html()
