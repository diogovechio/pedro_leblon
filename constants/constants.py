SECRETS_FILE = 'secrets.json'

WEATHER_LIST = ["previsao", "previsão", "tempo", "clima", " sol", "chover", "chuva"]

WEATHER_PROMPT = "responda as perguntas abaixo de forma enumerada. " \
                 "caso a informação perguntada não esteja na mensagem, você irá responder apenas isso: 'null'.\n" \
                 "responda diretamente a pergunta, sem comentários adicionais, " \
                 "segue o exemplos da estrutura que você deve responder:\n\n" \
                 "exemplo 1:\n" \
                 "1 - sim\n" \
                 "2 - rio de janeiro\n" \
                 "3 - 5 dias\n\n" \
                 "exemplo 2:\n" \
                 "1 - não\n" \
                 "2 - null\n" \
                 "3 - null\n\n" \
                 "exemplo 3:\n" \
                 "1 - sim\n" \
                 "2 - null\n" \
                 "3 - 3 dias\n\n" \
                 "exemplo 4:\n" \
                 "1 - sim\n" \
                 "2 - são paulo\n" \
                 "3 - null\n\n" \
                 "segue abaixo as perguntas em relação a mensagem:\n" \
                 "1 - foi solicitado uma previsão do tempo? - responda apenas 'sim' ou 'não''\n" \
                 "2 - qual local mencionado na mensagem? - responda apenas o nome do local por extenso, por exemplo: 'rio de janeiro', 'são paulo' ou 'null'\n" \
                 "3 - qual período em dias mencionado? - 'responda sempre os número de dias em dígitos, por exemplo: '3 dias'\n"

DRUNK_DECAPTOR_LIST = [
    'vai dormir merda',
    'senhor dono da verdade',
    'culpa dos webdevs',
    'mimimi webdevs python nojo',
    'mimimi',
    'tenho 99% de certeza que a ia tá errada',
    'bolsominion de merda alcoolatra',
    'minha indiferença é maior que meu desgosto',
    'eu pelo menos sou imparcial o suficiente pra enxergar essas coisas',
    'eu uso win 7 sem antivirus mais de uma década',
    'eu to ficando com raiva com todo mundo que manda merda pros meus comentários',
    'já vai arrumar problema com a polícia de novo?',
]

ASK_PHOTOS = ['melhorar', 'fotos', 'foto', 'melhorou']

MOCK_EDITS = ["editou pq", "eu vi oq vc escreveu", "preferia antes", "escreve direito da próxima vez"]

DECAPTOR_DISAPPOINTS = [' lula ', 'esquerdista', ' fato', 'venezuela', 'hipócrita', 'hipocrisia', 'hipocrita', 'dilma',
                        'imparcial']

SWEAR_WORDS = [' viado', 'porra', 'fuck', 'cock', 'transar', 'buceta', 'boceta',
                      'piroca', 'pornô', 'porno', 'sexo', 'cu?', ' cu ', 'caralho', 'foder', 'pinto',
                      'cú', 'chupa meu', 'chupa um', 'penis', 'pênis', 'chupa o', 'o saco do']

OPENAI_REACT_WORDS = ['bolsonaro', 'segundo turno', 'macho', ' lula ', 'dilma', 'homem', 'homens', 'ovni', 'votação',
                      'eleição', 'eleições', 'bosta', 'aliens', 'temer', ' et ', ' ets ', ' pt' ' et']

OPENAI_TRASH_LIST = ['"', "r:", "o:", "a:", "q:"]

CHATGPT_BS = ["não,", "lololo", "a comentar sobre", "não vou", "não irei", "linguagem natural", "desculpe", "assistente de", "virtual", "uma ia", "de ia", "como ia", "como uma ai", "como ai,", "de ai,", "openai", "como um modelo", "de linguagem", "não posso", "julgamentos pessoais", "inteligência artificial", "sem viés político", "modelo de"]

OPENAI_PROMPTS = {
    'fale': 'fale brevemente sobre esse tema:',
    'responda': 'responda brevemente isso:',
    'comente': 'comente objetivamente sobre isso:',
    'critique': 'critique o linguajar dessa mensagem:',
    'critique_reformule': 'critique o linguagem dessa mensagem e reformule para uma forma apropriada:',
    'critique_negativamente': 'comente negativamente em relação a esse tema:',
    'previsao_tempo': 'use emoji 🔥 para indicar temperaturas acima de 31 graus. emoji de 🌧 para indicar chuva. '
                      'emoji de ⛈ para indicar tempestade. emoji de ☀️ para indicar sol. '
                      'emoji de 🌥 para indicar sol entre nuvens. emoji de ☁️ para indicar tempo nublado. '
                      'agora resuma em 3 frases essa previsão metereológica:',
    'previsao_tempo_sensacionalista': 'use emoji 🔥 para indicar temperaturas acima de 25 graus. '
                                      'emoji de 🌧 para indicar chuva. emoji de ⛈ para indicar tempestade. '
                                      'emoji de ☀️ para indicar sol. emoji de 🌥 para indicar sol entre nuvens. '
                                      'emoji de ☁️ para indicar tempo nublado. '
                                      'agora resuma essa previsão metereológica de maneira sensacionalista, '
                                      'sem usar aspas:'
}

BOLSOFF_LIST = [
    'pro bolsonaro ir pro caralho',
    'pro jair já ir embora',
    'pro brasil voltar a ser comunista',
    'pra completar os 100 anos de sigilo do bolsonaro'
]

NEWS_WORD_LIST = ['pt', 'lula', 'eleicao', 'eleicoes', 'voto', 'dilma', 'bolsonaro', 'moro']


ANNUAL_DATE_PATTERN = r'^(0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[012])'
ONCE_DATE_PATTERN = r'^(0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[012])\/([2-9][0-9][0-9][0-9])$'

