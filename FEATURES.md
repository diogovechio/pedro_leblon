# Pedro Leblon Bot - Visão Geral das Funcionalidades

Este documento apresenta uma visão geral de todas as funcionalidades (features) do Pedro Leblon Bot, indicando os módulos do código responsáveis por gerenciar e executar cada uma delas.

---

## 1. Conversação Geral e Chat com IA
O bot pode conversar de forma natural com os usuários nos chats permitidos. Ele adota uma persona informal de "usuário de internet": sarcástico, inteligente, utilizando iniciais minúsculas e evitando pontuações excessivas ou formalidades desnecessárias.
*   **Gatilhos de Conversa**: Menções ao nome "Pedro", respostas a mensagens dele ou de forma aleatória com base em flags diárias.
*   **Comando `/pedro <mensagem>`**: Permite enviar um prompt direto para conversar com o bot utilizando o histórico recente como contexto.
*   **Respostas Duplas (Follow-up)**: Há uma chance aleatória de o bot enviar uma segunda mensagem complementar logo após responder.
*   **Módulos Responsáveis**:
    *   `pedro/brain/reactions/main/default_pedro.py` (Tratamento padrão de resposta/reação)
    *   `pedro/brain/reactions/pedro_command.py` (Tratamento do comando `/pedro`)
    *   `pedro/brain/reactions/main/agent_common.py` (Orquestração do agente)
    *   `pedro/brain/modules/llm.py` (Interface com a API de LLM da OpenAI)

---

## 2. Agente Autônomo (ReAct Agent)
Para responder a perguntas complexas, o bot inicializa um agente autônomo baseado no padrão ReAct (Thought -> Action -> Observation) que decide dinamicamente quais ferramentas utilizar para obter informações.
*   **Ferramentas Integradas**:
    *   `WeatherTool`: Consulta previsões do tempo.
    *   `ChatHistorySearchTool`: Busca termos ou assuntos específicos no histórico de mensagens do chat.
    *   `BirthdaySearchTool`: Consulta aniversários agendados.
    *   `PoliticalOpinionsTool`: Acessa informações de preferências ou opiniões políticas.
    *   `WebSearchTool`: Realiza pesquisas na web.
    *   `TaskListTool`: Gerencia as tarefas do usuário ou do grupo diretamente por meio do agente.
*   **Módulos Responsáveis**:
    *   `pedro/brain/agent/core.py` (Motor do ReAct Loop)
    *   `pedro/brain/agent/tools/` (Subpasta contendo a lógica de cada ferramenta)

---

## 3. Gerenciamento de Agenda e Aniversários
Permite agendar lembretes periódicos ou de ocorrência única nos grupos.
*   **Comando `/agendar <lembrete> <data>`**: Cria um agendamento com três tipos de frequências automáticas detectadas pela data:
    *   *Anual* (formato `DD/MM`)
    *   *Mensal* (formato `DD`)
    *   *Uma vez* (formato `DD/MM/YYYY`)
*   **Comando `/agenda`**: Exibe uma lista com todas as tarefas e lembretes agendados no chat, incluindo seus respectivos IDs.
*   **Comando `/aniversario <@username ou Nome> <data>`**: Cadastra um aniversário recorrente anual (formato `DD/MM`).
*   **Comando `/delete <id_do_agendamento>`**: Permite remover um item da agenda (restrito ao usuário que criou o agendamento).
*   **Módulos Responsáveis**:
    *   `pedro/brain/reactions/agenda_commands.py` (Gatilhos de comandos do Telegram)
    *   `pedro/brain/modules/agenda.py` (Persistência e lógica de negócio dos agendamentos)

---

## 4. Lista de Tarefas (To-Do List)
O bot permite gerenciar afazeres pessoais dos membros ou tarefas coletivas do grupo.
*   **Comando `/tarefa <descrição>`**: Adiciona uma tarefa pessoal para o usuário que enviou o comando.
*   **Comando `/tarefas`**: Lista as tarefas pessoais pendentes do usuário no chat.
*   **Comando `/tarefa_grupo <descrição>`**: Adiciona uma tarefa para o grupo.
*   **Comando `/tarefas_grupo`**: Lista todas as tarefas ativas do grupo e indica quem as criou.
*   **Comando `/concluir <id_da_tarefa>`**: Remove a tarefa concluída. Tarefas pessoais só podem ser concluídas por quem as criou, enquanto as do grupo podem ser finalizadas por qualquer membro.
*   **Módulos Responsáveis**:
    *   `pedro/brain/reactions/task_commands.py` (Gatilhos de comandos do Telegram)
    *   `pedro/brain/modules/task_list.py` (Gerenciador e banco de dados de tarefas)

---

## 5. Resumos e TL;DR
Gera resumos inteligentes sobre as mensagens do chat, ideal para quando os usuários entram em discussões longas.
*   **Comando `/tldr`**: Resumo em formato de parágrafo.
    *   Se usado em resposta a uma mensagem/imagem, resume o conteúdo da mensagem respondida.
    *   Se incluir argumentos (como número de dias ou menção a um usuário, ex.: `/tldr 3 @usuario`), resume as mensagens daquele usuário ou período de tempo.
    *   Caso contrário, resume o chat desde a última participação ativa do usuário que enviou o comando.
*   **Comando `/tlsr`**: Gera um resumo enxuto no formato de até 7 tópicos curtos (máximo de 6 palavras por tópico).
*   **Comando `/tlfr`**: Produz um resumo sob uma ótica intencionalmente distorcida e sensacionalista.
*   **Renomeação Automática do Chat**: Em chats específicos (configuráveis), o bot sugere e altera automaticamente o título do grupo com base no resumo gerado.
*   **Módulos Responsáveis**:
    *   `pedro/brain/reactions/summary_reactions.py` (Decisão de escopo e chamadas ao LLM)
    *   `pedro/brain/modules/chat_history.py` (Resgate do histórico do banco de dados)

---

## 6. Fact-Checking Marxista-Materialista
Permite verificar informações utilizando um filtro ideológico específico.
*   **Comandos `/refute`, `/fact` ou `/check`**: Avalia o argumento de uma mensagem respondida (ou de uma imagem/legenda) sob a perspectiva do materialismo histórico e dialético marxista. O bot desconstrói a afirmação e emite um contra-argumento focado na defesa da classe trabalhadora.
*   **Módulos Responsáveis**:
    *   `pedro/brain/reactions/fact_check.py` (Prompts estruturados e disparo)
    *   `pedro/brain/modules/llm.py` (Geração do texto analítico)

---

## 7. Análise de Imagens e Documentos
O bot processa arquivos de mídia enviados nos chats.
*   **Moderação Política Automática**: Quando usuários específicos da lista negra enviam imagens, o bot verifica se há conteúdo político ou referência a políticos. Se positivo, reage com um emoji de 💩 e executa o fact-check automático.
*   **Interações Multimodais**: Se o usuário enviar uma imagem e marcar o Pedro, o agente processa a imagem como entrada visual para gerar a resposta.
*   **Módulos Responsáveis**:
    *   `pedro/brain/reactions/main/images_reactions.py` (Detecção e moderação de imagem)
    *   `pedro/brain/modules/telegram.py` (Download e processamento da mídia da API do Telegram)
    *   `pedro/brain/modules/llm.py` (Suporte multimodal com o modelo da OpenAI)

---

## 8. Moderação de Palavrões (Complain Swearwords)
Se detectar palavras ofensivas ou palavrões nas mensagens dos usuários:
*   **Ação**: Há uma chance de 25% de o bot intervir criticando o linguajar, reformulando a frase para uma linguagem adequada usando inteligência artificial, ou respondendo com uma frase sarcástica gerada aleatoriamente a partir de um repositório pré-definido ("roletas da pavuna").
*   **Módulos Responsáveis**:
    *   `pedro/brain/reactions/complain_swearword.py` (Filtro e lógica de disparo)
    *   `pedro/brain/constants/constants.py` (Lista de termos proibidos - `SWEAR_WORDS`)
    *   `pedro/utils/text_utils.py` (Utilitário para carregar frases e ajustar texto)

---

## 9. Sistema de Humor, Afinidade e Ódio (User Data Manager)
O bot constrói opiniões e mede o nível de afinidade com cada usuário que interage no grupo de forma dinâmica.
*   **Análise de Sentimento**: A cada nova mensagem, o bot analisa o tom e atualiza no banco de dados o score de relacionamento com o autor da mensagem.
*   **Comando `/me`**: Mostra o ID do usuário, o ID do chat, o nível de ódio acumulado pelo bot contra ele e um resumo em poucas palavras do que o bot pensa ou sabe sobre ele.
*   **Comando `/puto`**: Pedro responde descrevendo (com deboche, ou em formato de poema) o quanto está irritado ou contente com o usuário que enviou o comando, sem citar números da escala diretamente.
*   **Comando `/putos`**: Mostra a lista dos usuários com os quais Pedro está atualmente mais irritado (score de ódio elevado), com reclamações personalizadas.
*   **Provocações Aleatórias (Tease Messages)**: Chance diária de o bot mandar mensagens de zuação personalizadas para um usuário, baseadas em fatos salvos sobre ele.
*   **Módulos Responsáveis**:
    *   `pedro/brain/modules/user_data_manager.py` (Armazenamento, opiniões e ajuste de afinidade)
    *   `pedro/brain/reactions/misc_commands.py` (Tratamento de `/me`, `/puto` e `/putos`)
    *   `pedro/brain/reactions/random_reactions.py` (Disparo diário de provocações)

---

## 10. Reações de Emojis e Enquetes Automáticas
Garante que o bot reaja silenciosamente com emojis no Telegram a certas mensagens.
*   **Reações Políticas**: Reage com 💩, 🤡, ou 🤪 a mensagens de cunho político de usuários monitorados.
*   **Reações de Elogios**: Reage com 🎉, 👏, 🏆, 🍾, ❤, ou 💯 a elogios e felicitações.
*   **Reações LGBTQIA+**: Reage com 💅, 🦄, 🌭, 👀, ou 🌚 a termos queer.
*   **Enquetes (Polls)**: Reage automaticamente com 💩 a qualquer enquete criada no grupo.
*   **Módulos Responsáveis**:
    *   `pedro/brain/reactions/emoji_reactions.py`
    *   `pedro/brain/reactions/poll_reaction.py`

---

## 11. Críticas e Elogios sob Demanda
*   **Comandos `/critique`, `/elogie`, `/simpatize` ou `/humilhe`**: Devem ser usados em resposta a uma mensagem de outro usuário. Pedro usará inteligência artificial para repreender, parabenizar, simpatizar ou ridicularizar aquela mensagem específica e o autor dela.
*   **Módulos Responsáveis**:
    *   `pedro/brain/reactions/critic_or_praise.py`

---

## 12. Previsão do Tempo
*   **Comando `/previsao <cidade>` ou `/prev <cidade>`**: Busca a previsão do tempo para 7 dias da cidade desejada. Caso nenhuma cidade seja especificada, ele tenta usar a última cidade consultada pelo mesmo usuário.
*   **Módulos Responsáveis**:
    *   `pedro/brain/reactions/weather_commands.py` (Interface de comando)
    *   `pedro/utils/weather_utils.py` (Integração com a API do OpenWeatherMap)

---

## 13. Comandos Administrativos e Utilitários
*   **Comando `/del`**: Permite apagar mensagens. Se for usado em resposta a uma mensagem própria ou do próprio Pedro, apaga ambas do chat. Se usado em resposta à mensagem de outro usuário, o bot recusa, gera uma crítica pesada e ameaça banir o usuário daquele chat.
*   **Comando `/dorme`**: Coloca o bot para "cochilar" (congela o processamento de respostas) durante 5 minutos.
*   **Comando `/data`**: Extrai o banco de dados atual do bot em formato JSON e o envia como documento para um chat privado com o administrador.
*   **Comando `/version`**: Exibe a versão atualizada do Pedro Bot.
*   **Módulos Responsáveis**:
    *   `pedro/brain/reactions/misc_commands.py`
    *   `pedro/data_structures/daily_flags.py` (Lógica de congelamento/freeze mode)
