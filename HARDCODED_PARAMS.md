# Análise de Parâmetros Hardcoded

Este documento detalha os parâmetros hardcoded encontrados no código-fonte do projeto Pedro Leblon Bot. Para aumentar a flexibilidade e permitir que o bot seja genérico e configurável, esses valores devem ser movidos para arquivos de configuração, como `bot_configs.json`.

## 1. Módulos Principais (`pedro/brain/modules/`)

### 1.1. `agenda.py`

- **Caminho do Banco de Dados:**
  - **Local:** `AgendaManager.__init__`
  - **Valor:** `"database/pedro_database.json"`
  - **Sugestão:** Mover para `bot_configs.json` para permitir que o local do banco de dados da agenda seja configurável.

- **Caminho dos GIFs:**
  - **Local:** `AgendaManager.check_agenda`
  - **Valor:** `'gifs/birthday0.mp4'`
  - **Sugestão:** O caminho para os GIFs de aniversário deve ser configurável, permitindo adicionar ou alterar a mídia utilizada.

- **Lógica de Notificação:**
  - **Local:** `AgendaManager.check_agenda`
  - **Valores:** O intervalo de `asyncio.sleep(10)` e a lógica para determinar o último dia do mês (para lembretes do dia 31) estão hardcoded.
  - **Sugestão:** O intervalo de verificação da agenda e talvez a lógica de "último dia do mês" poderiam ser parametrizados para diferentes casos de uso.

### 1.2. `chat_history.py`

- **Diretório de Logs de Chat:**
  - **Local:** `ChatHistory.__init__`
  - **Valor:** `"database/chat_logs"`
  - **Sugestão:** Permitir a configuração do diretório onde os logs de chat são armazenados.

- **Modelos de LLM para Imagens:**
  - **Local:** `ChatHistory._process_image`
  - **Valores:** `"gpt-4.1-nano"` e `"gpt-4.1-mini"`
  - **Sugestão:** Os modelos de LLM usados para descrever imagens devem ser configuráveis, permitindo a escolha de modelos mais adequados ou mais recentes.

- **Prompts de Imagem:**
  - **Local:** `ChatHistory._process_image`
  - **Valores:** `"Faça uma curta descrição da imagem, máximo 10 palavras."` e outros.
  - **Sugestão:** Os prompts usados para a análise de imagem poderiam ser externalizados para um arquivo de prompts ou para a configuração principal.

### 1.3. `database.py`

- **Nome do Banco de Dados Padrão:**
  - **Local:** `Database.__init__`
  - **Valor:** `"pedro_database.json"`
  - **Sugestão:** O nome padrão do arquivo de banco de dados deve ser configurável.

- **Limite de Backups:**
  - **Local:** `Database._create_backup`
  - **Valor:** `5`
  - **Sugestão:** O número de backups a serem mantidos deve ser um parâmetro configurável.

### 1.4. `llm.py`

- **Modelo de LLM Padrão:**
  - **Local:** `LLM.__init__`
  - **Valor:** `"gpt-4.1-nano"`
  - **Sugestão:** O modelo padrão deve ser definido no arquivo de configuração.

- **Endpoint da API OpenAI:**
  - **Local:** `LLM._prepare_web_search_request`, `LLM._prepare_chat_model_request`, etc.
  - **Valor:** `"https://api.openai.com/v1/..."`
  - **Sugestão:** Embora raramente mude, o endpoint da API poderia ser configurável para suportar proxies ou versões diferentes da API.

### 1.5. `scheduler.py`

- **Horários das Tarefas:**
  - **Local:** `Scheduler.start`
  - **Valores:** `"15:00"`, `"22:00"`, `"21:00"`, `"19:00"`
  - **Sugestão:** Os horários para as tarefas agendadas (processamento de histórico, backup, etc.) devem ser configuráveis.

- **ID do Chat para Backup:**
  - **Local:** `Scheduler._run_database_backup`
  - **Valor:** `8375482`
  - **Sugestão:** O ID do chat para onde o backup do banco de dados é enviado deve ser definido no `bot_configs.json`.

### 1.6. `telegram.py`

- **Endpoint da API Telegram:**
  - **Local:** `Telegram.__init__`
  - **Valor:** `"https://api.telegram.org/bot{token}"`
  - **Sugestão:** Similar ao endpoint da OpenAI, poderia ser configurável para casos de uso específicos (proxies, etc.).

- **Limite de Retentativas e Tempo de Espera:**
  - **Local:** Vários métodos como `send_photo`, `send_message`.
  - **Valores:** `max_retries=5`, `asyncio.sleep(10)`
  - **Sugestão:** Os parâmetros de retentativa e os tempos de espera poderiam ser ajustáveis.

### 1.7. `user_data_manager.py`

- **Níveis de Sentimento (Prompts):**
  - **Local:** `UserDataManager.__init__`
  - **Valores:** Lista de prompts como `"Responda de maneira sucinta..."`
  - **Sugestão:** Estes prompts que definem o comportamento do bot com base no sentimento devem ser configuráveis.

- **Intervalo de Decaimento de Sentimento:**
  - **Local:** `UserDataManager.sentiment_decay_loop`
  - **Valor:** `asyncio.sleep(1200)` (20 minutos) e `-0.1` de ajuste.
  - **Sugestão:** A taxa e o intervalo de decaimento do sentimento devem ser parametrizáveis.

- **Reações de Emoji por Tom:**
  - **Local:** `UserDataManager.adjust_sentiment`
  - **Valores:** `["🤬", "😡", "🖕"]`, `["🆒", "🗿"]`, etc.
  - **Sugestão:** As reações de emoji para cada tom de mensagem poderiam ser definidas na configuração.

## 2. Reações (`pedro/brain/reactions/`)

### 2.1. `complain_swearword.py`

- **Probabilidades de Reação:**
  - **Local:** `complain_swearword_reaction`
  - **Valores:** `random.random() < 0.25`
  - **Sugestão:** A probabilidade de reclamar de um palavrão ou de enviar uma reação aleatória deve ser configurável.

- **Prompts de Crítica:**
  - **Local:** `complain_swearword_reaction`
  - **Valores:** Dicionário `prompts` com valores como `'Critique o linguajar dessa mensagem:'`.
  - **Sugestão:** Mover para um arquivo de prompts ou para a configuração.

### 2.2. `critic_or_praise.py`

- **Prompts de Comando:**
  - **Local:** `_critic_or_praise`
  - **Valores:** F-strings que montam os prompts como `f"{'dê uma bronca em' if round(random.random()) else 'xingue o'} {user_name}..."`
  - **Sugestão:** As variações de prompts para os comandos `/critique`, `/elogie`, etc., poderiam ser externalizadas.

### 2.3. `emoji_reactions.py`

- **Palavras-gatilho e Usuários-alvo:**
  - **Local:** `political_trigger`, `congratulations_trigger`, `lgbt_trigger`
  - **Valores:** Listas como `political_words`, `target_users`, `congrats_words`, `lgbt_words`.
  - **Sugestão:** Todas essas listas devem ser movidas para `bot_configs.json` para permitir fácil customização das reações automáticas de emoji.

### 2.4. `misc_commands.py`

- **ID do Chat para /data:**
  - **Local:** `handle_data_command`
  - **Valor:** `8375482`
  - **Sugestão:** O ID do chat para onde os dados são enviados deve ser configurável.

### 2.5. `summary_reactions.py`

- **ID do Chat para Mudança de Título:**
  - **Local:** `update_chat_title`
  - **Valor:** `-1001369599178`
  - **Sugestão:** O ID do chat cujo título pode ser alterado dinamicamente deve ser configurável.

- **Prompts de Resumo:**
  - **Local:** `handle_reply_to_message`, `handle_command_with_parameters`, etc.
  - **Valores:** Vários prompts como `"faça um resumo do texto a seguir:"`.
  - **Sugestão:** Externalizar os prompts de resumo.

## 3. Constantes (`pedro/brain/constants/`)

### 3.1. `constants.py`

- **`SWEAR_WORDS`:** A lista de palavrões deve ser configurável por chat ou globalmente.
- **`POLITICAL_WORDS` e `POLITICAL_OPINIONS`:** As palavras e opiniões políticas são específicas do "Pedro" e devem ser movidas para a configuração para permitir um bot mais genérico.

## 4. Utilitários (`pedro/utils/`)

### 4.1. `prompt_utils.py`

- **ID do Chat de Log:**
  - **Local:** `send_telegram_log`
  - **Valor:** `-1002051541243`
  - **Sugestão:** O ID do chat de log de prompts deve ser configurável.

- **Lógica de Gatilho de Texto (`text_trigger`):**
  - **Valores:** A probabilidade `random.random() < 0.15` e as condições de início/fim de mensagem (`.startswith("pedro")`) são hardcoded.
  - **Sugestão:** A probabilidade e as palavras-chave para acionar o bot poderiam ser configuráveis.

### 4.2. `text_utils.py`

- **URL do `get_roletas_from_pavuna`:**
  - **Local:** `get_roletas_from_pavuna`
  - **Valor:** `"https://keyo.me/bot/roleta.json"`
  - **Sugestão:** A URL para obter mensagens aleatórias deve ser configurável.

### 4.3. `weather_utils.py`

- **Local Padrão:**
  - **Local:** `get_forecast`
  - **Valor:** `"russia"`
  - **Sugestão:** O local padrão para a previsão do tempo, caso nenhum seja fornecido, deve ser configurável.

## Conclusão

A refatoração desses pontos, movendo os valores hardcoded para o arquivo `bot_configs.json`, aumentará significativamente a modularidade, a capacidade de configuração e a generalidade do bot, alinhando-se com o objetivo do projeto.
