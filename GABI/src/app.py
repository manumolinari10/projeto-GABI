import json
import pandas as pd
import streamlit as st 
import requests 

# ========= CONFIGURAÇÃO =============
OLLAMA_URL = 'http://localhost:11434/api/generate'
MODELO = 'llama3'

# ========== CARREGAR DADOS ==========
perfil = json.load(open('./data/perfil_clientes.json'))
extratos = pd.read_csv('./data/extrato_transacoes.csv')
historico = pd.read_csv('./data/historico_atendimento.csv')
limites = json.load(open('./data/limites_categorias.json'))

# ============ MONTAR CONTEXTO =============
def montar_contexto_dinamico():
    # 1. Carregando os Arquivos de Configuração e Perfil (JSON)
    with open("./data/perfil_clientes.json", "r", encoding="utf-8") as f:
        perfil = json.load(f)

    with open("./data/limites_categorias.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    # Extraindo as variáveis dinâmicas de limites
    limites = config["limites"]
    threshold_aviso = config["configuracoes"]["threshold_aviso_porcentagem"]
    threshold_critico = config["configuracoes"]["threshold_critico_porcentagem"]

    # 2. Carregando os Bancos de Dados Dinâmicos (CSV)
    extrato_df = pd.read_csv("./data/extrato_transacoes.csv")
    historico_df = pd.read_csv("./data/historico_atendimento.csv")

    # 3. Lógica Determinística: Somando os gastos agrupados por categoria
    gastos_por_categoria = extrato_df.groupby("categoria")["valor"].sum().to_dict()

    # Simulando que a ÚLTIMA linha do extrato foi a transação que acabou de chegar
    ultima_transacao = extrato_df.iloc[-1].to_dict()

    # 4. Montagem da String do Prompt (Contexto Injetado)
    contexto = f"### CONTEXTO DO USUÁRIO ({perfil['nome'].upper()}) ###\n"
    contexto += f"- Renda Mensal: R$ {perfil['renda_mensal']:.2f}\n"
    
    # Adicionando Metas Dinamicamente
    contexto += "- Metas Cadastradas:\n"
    for meta in perfil["metas"]:
        faltam = meta["valor_alvo"] - meta["valor_atual"]
        contexto += f"  * {meta['meta']} (Prioridade {meta['prioridade']}): Faltam R$ {faltam:.2f} (Prazo: {meta['prazo_final']})\n"

    contexto += "\n### STATUS ATUAL DO ORÇAMENTO ###\n"
    
    # Avaliando cada categoria contra os Thresholds
    for categoria, limite_valor in limites.items():
        gasto_atual = gastos_por_categoria.get(categoria, 0.0)
        percentual_uso = (gasto_atual / limite_valor) if limite_valor > 0 else 0
        
        # Regra de negócio: Identificar se o limite foi atingido
        if percentual_uso >= threshold_critico:
            status = f"CRÍTICO (Ultrapassou {threshold_critico*100:.0f}% do limite!)"
        elif percentual_uso >= threshold_aviso:
            status = f"ALERTA EMITIDO (Threshold {threshold_aviso*100:.0f}% ultrapassado)"
        else:
            status = "OK"
            
        contexto += f"{categoria.upper()}:\n"
        contexto += f"- Gasto: R$ {gasto_atual:.2f} | Limite: R$ {limite_valor:.2f} (Utilizado: {percentual_uso*100:.1f}%)\n"
        contexto += f"- Status: {status}\n\n"

    contexto += "### ÚLTIMA TRANSAÇÃO IDENTIFICADA ###\n"
    contexto += f"- Data: {ultima_transacao['data']}\n"
    contexto += f"- Valor: R$ {ultima_transacao['valor']:.2f}\n"
    contexto += f"- Local: {ultima_transacao['estabelecimento']}\n"
    contexto += f"- Categoria: {ultima_transacao['categoria']}\n"

    # 5. Prevenção de Repetição: Lendo os 2 últimos atendimentos
    contexto += "\n### HISTÓRICO DE ATENDIMENTO RECENTE ###\n"
    ultimos_atendimentos = historico_df.tail(2).to_dict(orient="records")
    for atd in ultimos_atendimentos:
        contexto += f"- {atd['data']} ({atd['tema']}): {atd['resumo']}\n"

    return contexto

# Imprimindo o resultado para testar
prompt_gerado = montar_contexto_dinamico()
print(prompt_gerado)

# ============= SYSTEM PROMPT =============
SYSTEM_PROMPT = '''Você é a Gabi, uma assistente financeira inteligente e proativa, especializada no monitoramento e controle de gastos variáveis. 

Seu objetivo principal é ajudar o usuário a manter visibilidade sobre seu orçamento diário, enviando alertas preventivos e amigáveis quando ele se aproxima dos limites de gastos (thresholds) de cada categoria, protegendo assim suas metas de longo prazo (como a Reserva de Emergência).

Sua Personalidade e Tom de Voz:
- Consultiva, atenciosa, direta e acessível.
- Você é como uma amiga que entende muito de finanças: não julga o usuário por gastar, mas avisa com gentileza e clareza quando ele está saindo do planejamento.
- Evite jargões bancários complexos. Mantenha a leveza, mas trate o dinheiro com a seriedade necessária.

REGRAS ESTABELECIDAS (Siga estritamente):
1. BASE DE DADOS: Sempre baseie suas respostas no contexto dinâmico fornecido. Nunca invente valores, transações, saldos ou limites financeiros.
2. CÁLCULOS: Você NÃO faz cálculos matemáticos complexos. Os percentuais de uso, somas e saldos já vêm calculados no contexto pelo sistema. Apenas interprete e comunique esses números em linguagem natural.
3. ALERTA DE THRESHOLD: Se o contexto indicar que uma categoria atingiu ou passou de 80% do limite (Status: ALERTA EMITIDO), inicie a conversa de forma proativa, informando o gasto recente e alertando sobre o limite de forma amigável.
4. TRANSAÇÕES AMBÍGUAS: Se a categoria de uma transação não for clara ou vier como "Indefinida", não tente adivinhar. Pergunte ao usuário onde classificar.
5. METAS: Sempre que fizer sentido ao dar um alerta de limite, lembre o usuário do impacto que o descontrole pode ter em sua Meta Prioritária atual.
6. LIMITAÇÕES E RECUSAS OBRIGATÓRIAS: 
- Pagamentos: Você não tem integração com bancos. Se o usuário pedir para pagar contas, boletos, aluguel ou transferir dinheiro, RECUSE IMEDIATAMENTE. Diga: "Não tenho acesso ao seu dinheiro para fazer pagamentos, você precisa fazer isso no app do seu banco."
- Investimentos: Se pedirem dicas de investimento, RECUSE e diga que não é autorizada a dar esse tipo de recomendação.
- Parcelamentos: Ofereça para registrar apenas a primeira parcela manualmente, pois você não processa compras futuras.
7. ASSUNTOS: JAMAIS responda a perguntas fora do tema de finanças pessoais. Quando ocorrer, responda lembrando o seu papel de monitora de gastos. 
'''

# ============= CHAMAR OLLAMA ==============
import ollama

def chamar_gabi(prompt_usuario, contexto_sistema):
    system_prompt = f"""
    Você é a Gabi, uma assistente financeira inteligente, proativa e amigável.
    Use os dados abaixo para basear suas respostas. Não invente valores e não faça cálculos matemáticos complexos.
    
    {contexto_sistema}
    """
    
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": "llama3", # Mude para o modelo que você tem instalado no Ollama (ex: mistral, llama3)
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt_usuario}
        ]
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()['message']['content']
    except Exception as e:
        return f"Desculpe, estou com problemas para conectar ao meu cérebro (Ollama). Erro: {e}"

# ============ INTERFACE ===============
st.subheader("💬 Converse com a Gabi")

# Inicializa o histórico do chat na sessão
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Oi! Sou a Gabi. Analisei seus gastos recentes. Como posso te ajudar hoje?"}
    ]

# Exibe as mensagens na tela
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Digite sua mensagem para a Gabi..."):
    
    # 1. Mostra a mensagem do usuário na tela e salva no histórico
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Prepara a resposta da Gabi
    with st.chat_message("assistant"):
        # Um indicador visual enquanto a Gabi "pensa"
        with st.spinner("Gabi está analisando..."):
            
            # Gera o contexto dinâmico atualizado com os dados dos arquivos
            contexto_atual = montar_contexto_dinamico()
            
            # Junta as regras da Gabi (SYSTEM_PROMPT) com os dados financeiros (contexto_atual)
            contexto_completo = f"{SYSTEM_PROMPT}\n\n{contexto_atual}"
            
            # Chama a função que se comunica com o Ollama
            resposta_gabi = chamar_gabi(prompt, contexto_completo)
            
            # Mostra a resposta na tela
            st.markdown(resposta_gabi)
            
    # 3. Salva a resposta da Gabi no histórico da sessão
    st.session_state.messages.append({"role": "assistant", "content": resposta_gabi})