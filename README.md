# GABI - Assistente Financeira Inteligente 🤖

Gabi é uma assistente financeira conversacional construída com Streamlit e Ollama (LLM local). Ela monitora os gastos do usuário em tempo real, compara com limites por categoria e conversa de forma proativa e amigável para ajudar a manter o orçamento sob controle sem nunca inventar números.

# ✨ Funcionalidades

**Contexto dinâmico:** a cada mensagem, o app recalcula os gastos por categoria a partir do extrato de transações e monta um contexto atualizado para o modelo.

**Alertas de threshold:** cada categoria é avaliada contra dois limites configuráveis (aviso e crítico) e recebe um status (**OK**, **ALERTA EMITIDO** ou **CRÍTICO**).

**Acompanhamento de metas:** exibe metas financeiras do usuário (valor alvo, valor atual, prazo, prioridade) e relaciona alertas de gasto ao impacto nessas metas.

**Histórico de atendimento:** consulta os últimos atendimentos para evitar repetir orientações já dadas.

**Recusas de escopo obrigatórias:** a Gabi nunca faz pagamentos, não dá dicas de investimento e não calcula parcelamentos futuros — apenas orienta dentro do seu papel.

**Interface de chat** via **st.chat_message** / **st.chat_input**, com histórico mantido na sessão do Streamlit.


# 🧠 Como funciona


**montar_contexto_dinamico()** lê os arquivos de dados, soma os gastos por categoria, compara com os limites e monta uma string de contexto (perfil, orçamento, última transação e histórico recente).

Esse contexto é combinado com o **SYSTEM_PROMPT** (que define a personalidade da Gabi e suas regras de negócio).

**chamar_gabi()** envia o prompt do usuário + contexto para o Ollama, via **POST http://localhost:11434/api/chat**, usando o modelo **llama3**.

A resposta é exibida no chat e o histórico é mantido em **st.session_state**.


# 🚀 Como rodar

**1) Pré-requisitos**


Python 3.9+
Ollama instalado e rodando localmente
Um modelo baixado no Ollama (por padrão, llama3):


*bash* 

ollama pull llama3

**2) Instalação**

*bash*

pip install streamlit pandas requests ollama

**3) Preparar os dados**

Crie a pasta *data/* na raiz do projeto com os quatro arquivos descritos acima.

**4) Executar**

*bash*

streamlit run src/app.py

O app abrirá no navegador (geralmente em http://localhost:8501).

# ⚙️ Configuração

**As principais constantes ficam no topo do *app.py*:**

*python*

**OLLAMA_URL** = 'http://localhost:11434/api/generate'

**MODELO** = 'llama3'

Para usar outro modelo (ex: *mistral*), altere o valor de **MODELO** e o campo *"model"* dentro de **chamar_gabi()**.

# 📌 Limitações 


1 - Não realiza pagamentos, transferências ou qualquer operação bancária real.

2 - Não fornece recomendações de investimento.

3 - Não processa parcelamentos futuros (apenas registra a primeira parcela manualmente, conforme orientado no **SYSTEM_PROMPT**).

4 - Depende de uma instância local do Ollama rodando — não funciona sem ele.

5 - Os cálculos financeiros são feitos em Python (determinístico); o modelo apenas interpreta e comunica os números, sem fazer contas.

⚠️ **Perfil único e fixo:** o app depende do arquivo *perfil_clientes.json* para carregar os dados do usuário, mas atualmente ele não suporta múltiplos perfis — o código sempre lê o mesmo arquivo e assume um único cliente cadastrado (no exemplo deste projeto, João Silva). Não há seleção de usuário, login ou troca de perfil pela interface. Para simular outro cliente, é necessário editar manualmente o conteúdo de *perfil_clientes.json* e reiniciar o app.


# 🛠️ Possíveis melhorias futuras


1 - Suporte a múltiplos usuários/perfis.

2 - Persistência do histórico de chat entre sessões (hoje ele vive apenas em **st.session_state**).

3 - Testes automatizados para a lógica de **montar_contexto_dinamico()**.

4 - Configuração via variáveis de ambiente (**.env**) em vez de constantes fixas no código.
