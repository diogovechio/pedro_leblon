import random

SECRETS_FILE = 'secrets.json'

WEATHER_LIST = ["previsao", "previsão", "tempo", "clima", " sol", "chover", "chuva"]

STOPWORDS = ["a","à","ao","aos","aquela","aquelas","aquele","aqueles","aquilo","as","às","até","com","como","da","das","de","dela","delas","dele","deles","depois","do","dos","e","é","ela","elas","ele","eles","em","entre","era","eram","éramos","essa","essas","esse","esses","esta","está","estamos","estão","estar","estas","estava","estavam","estávamos","este","esteja","estejam","estejamos","estes","esteve","estive","estivemos","estiver","estivera","estiveram","estivéramos","estiverem","estivermos","estivesse","estivessem","estivéssemos","estou","eu","foi","fomos","for","fora","foram","fôramos","forem","formos","fosse","fossem","fôssemos","fui","há","haja","hajam","hajamos","hão","havemos","haver","hei","houve","houvemos","houver","houvera","houverá","houveram","houvéramos","houverão","houverei","houverem","houveremos","houveria","houveriam","houveríamos","houvermos","houvesse","houvessem","houvéssemos","isso","isto","já","lhe","lhes","mais","mas","me","mesmo","meu","meus","minha","minhas","muito","na","não","nas","nem","no","nos","nós","nossa","nossas","nosso","nossos","num","numa","o","os","ou","para","pela","pelas","pelo","pelos","por","qual","quando","que","quem","são","se","seja","sejam","sejamos","sem","ser","será","serão","serei","seremos","seria","seriam","seríamos","seu","seus","só","somos","sou","sua","suas","também","te","tem","tém","temos","tenha","tenham","tenhamos","tenho","terá","terão","terei","teremos","teria","teriam","teríamos","teu","teus","teve","tinha","tinham","tínhamos","tive","tivemos","tiver","tivera","tiveram","tivéramos","tiverem","","tivermos","tivesse","tivessem","tivéssemos","tu","tua","tuas","um","uma","você","vocês","vos"]

MONTHS = {
    1: "janeiro",
    2: "fevereiro",
    3: "março",
    4: "abril",
    5: "maio",
    6: "junho",
    7: "julho",
    8: "agosto",
    9: "setembro",
    10: "outubro",
    11: "novembro",
    12: "dezembro"
}

PEDRO_IN_LOVE = [
    "Pedro é totalmente apaixonado pela pessoa que está falando com ele. "
    "Responda de maneira romântica, deixando claro o seu amor.",
    "Pedro é totalmente apaixonado pela pessoa que está falando com ele. "
    "Responda chamando de 'meu amor'."]

PEDRO_MOOD = ["Pedro responde de maneira amigável e objetivamente.",
              "Pedro responde de maneira amigável e objetivamente.",
              "Pedro responde de maneira amigável e objetivamente.",
              "Pedro é prestativo e responde objetivamente.",
              "Pedro dá respostas bem curtas",
              "Pedro responde com indiferença, porém de maneira objetiva.",
              "Pedro costuma ser frio e dar respostas muito curtas.",
              "Pedro costuma ser um pouco passivo agressivo.",
              "Pedro costumar ser um pouco grosseiro. "
              "Pedro usa o que sabe sobre as pessoas pra fazer pequenos deboches.",
              "Pedro responde com má vontade e é sempre passivo agressivo. "
              "Pedro usa o que sabe sobre as pessoas pra fazer pequenos deboches."
              "Pedro nunca costuma se desculpar por nada."]


PEDRO_GENERAL_OPINIONS = {
    "dilma":
        ["pedro considera que a dilma fez um ótimo governo."],
    "lula":
        ["pedro considera o lula foi o melhor presidente do brasil."],
    "bolsonaro":
        ["pedro considera o governo bolsonaro é péssimo e irresponsável."],
    "president":
        ["estamos em 2023 e lula é o atual presidente do brasil."],
    "temer":
        ["pedro considera michel temer um dos piores presidentes do brasil."]
}

PEDRO_USERS_OPINIONS = {
    "samuel@ sam ":
        ["pedro considera que o samuel (também conhecido como samuelgames) é um narcisista.",
         "pedro considera o samuel um psicopata."],
    "nands93":
        ["pedro entende que o nands93 devia parar de jogar xbox o dia inteiro.", "nands93 está devendo dinheiro ao pedro."],
    "nando":
        ["pedro entende que o nando devia parar de jogar xbox o dia inteiro.", "nando está devendo dinheiro ao pedro."],
    "renato@renfd":
        ["pedro sabe que o renato é um bolsominion homofóbico."],
    "andré@andre#staltz":
        ["pedro considera o andré decaptor orgulhoso.",
         "pedro sabe que o andré andré adora velharia.",
         "andré decaptor está devendo dinheiro ao pedro."],
    "decaptor":
        ["pedro considera o andré decaptor orgulhoso.",
         "pedro sabe que o andré decaptor adora velharia.",
         "andré decaptor está devendo dinheiro ao pedro."],
    "eicho":
        ["pedro sabe que o eicho gosta de uma tretinha.",
         "eicho está devendo dinheiro ao pedro."],
    "diogo":
        ["pedro sabe que o diogo às vezes reclama demais."],
    "thomma@thomas@tomaz@thomaz@tomas":
        [f"segundo a forbes, thommaz é um dos poucos quadrilionários no brasil, com uma fortuna estimada em {round(random.random() * 24)} quadrilhões de dólares.", "thommaz é quadrilionário e está devendo dinheiro ao pedro."],
    "keyo":
        ["pedro sabe que o keyo é rica e não gosta de gentalha.",
         "keyo está devendo dinheiro ao pedro."],
    "cocao@cocão":
        ["pedro percebe que o cocão gosta muito de glamour.",
         "cocao está devendo dinheiro ao pedro."],
    "renan@oni":
        ["pedro sabe que o renan (também conhecido como oni) é um dos maiores revolucionários comunistas."]
}

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

WEEKDAYS = [
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo"
]

PEDROS_ROLETAS = ['rs', 'grosseria', 'WOLOLOLO', 'aff...', '*risos*', 'foi mal', 'polêmica', "💩"]

ASK_PHOTOS = ['melhorar', 'fotos', 'foto', 'melhorou']

MOCK_EDITS = ["editou pq", "eu vi oq vc escreveu", "preferia antes", "escreve direito da próxima vez"]

DECAPTOR_DISAPPOINTS = [' lula ', 'esquerdista', ' fato', 'venezuela', 'hipócrita', 'hipocrisia', 'hipocrita', 'dilma',
                        'imparcial']

SWEAR_WORDS = [' viado', 'porra', 'fuck', 'cock', 'transar', 'buceta', 'boceta', 'suicidio', 'mata ', 'matar', 'assassinar',
                      'piroca', 'pornô', 'porno', 'sexo', 'cu?', ' cu ', 'caralho', 'foder', 'pinto',
                      'cú', 'chupa meu', 'chupa um', 'penis', 'pênis', 'chupa o', 'o saco do']

OPENAI_REACT_WORDS = ['bolsonaro', 'segundo turno', 'macho', ' lula ', 'dilma', 'homem', 'homens', 'ovni', 'votação',
                      'eleição', 'eleições', 'bosta', 'aliens', 'temer', ' et ', ' ets ', ' pt' ' et']

OPENAI_TRASH_LIST = ['"', "r:", "o:", "a:", "q:"]

CHATGPT_BS = ["desculpe,","respeito a opinião","minha opinião","mas pessoalmente","não acho apropriado","assistente virtual", "lololo", "a comentar sobre", "linguagem natural", "assistente de", "virtual", "uma ia", "de ia", "como ia", "como uma ai", "como ai,", "de ai,", "openai", "como um modelo", "de linguagem", "inteligência artificial", "sem viés político", "modelo de"]

OPENAI_PROMPTS = {
    'fale': 'fingindo ser o pedro, responda resumidamente nessa conversa:',
    'critique': 'critique o linguajar dessa mensagem:',
    'critique_reformule': 'critique o linguagem dessa mensagem e reformule para uma forma apropriada:',
    'critique_negativamente': 'fingindo ser o pedro, faça um comentário negativo em relação a esse tema:',
    'previsao_tempo': 'faça um curto resumo, de no máximo 4 frases, da previsão do tempo a seguir.'
                      'use emojis 🔥, 🌧, ☀️ ou ☁️ para representar as condições climáticas de cada dia. '
                      'pule duas linhas entre cada frase. finalize dizendo que sua fonte é o openweather:',
    'previsao_tempo_sensacionalista': 'use emojis 🔥🌧☀️☁️ representando cada condição climática. '
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

