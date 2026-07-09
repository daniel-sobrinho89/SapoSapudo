import json
import random


class LivroClimatico:
    def __init__(self):
        with open("data/livro_climatico.json", encoding="utf-8") as arquivo:
            self.frases = json.load(arquivo)

    def gerar_texto_narracao(self, clima):
        temperatura = getattr(clima, "temperature", 0)
        umidade = getattr(clima, "humidity", 0)
        velocidade_vento = getattr(clima, "wind_speed", 0)
        direcao_vento = self.obter_direcao_vento(getattr(clima, "wind_direction", 0))
        nuvens = getattr(clima, "cloudiness", 0)
        previsao_nuvens = getattr(clima, "future_cloudiness_3h", nuvens)

        historias = []

        historias.append(
            f"Hum... este velho livro climático resolveu contar uma história sobre o dia de hoje. "
            f"O lago acordou com {temperatura:.0f} graus, enquanto uma brisa vinda do {direcao_vento} "
            "deslizava entre os juncos. "
            f"As nuvens ocupam cerca de {nuvens:.0f} por cento do céu e a umidade chegou a {umidade:.0f} por cento. "
            "Parece que a natureza decidiu escrever mais um capítulo tranquilo."
        )

        historias.append(
            "Curioso... este capítulo fala sobre um sapo muito antigo que dizia prever o tempo apenas observando as libélulas. "
            f"Hoje ele certamente diria que a temperatura está em {temperatura:.0f} graus, "
            f"com o vento soprando do {direcao_vento}. "
            f"O céu apresenta aproximadamente {nuvens:.0f} por cento de nuvens. "
            "Talvez aquele velho sapo realmente soubesse de alguma coisa."
        )

        historias.append(
            "Esta página parece ter sido escrita por um poeta. "
            f"Ela conta que o lago respira suavemente sob uma temperatura de {temperatura:.0f} graus. "
            f"O vento vindo do {direcao_vento} leva consigo o perfume da mata. "
            f"A umidade alcançou {umidade:.0f} por cento e as nuvens passeiam lentamente pelo céu. "
            "Nem toda previsão serve apenas para avisar sobre chuva. Algumas existem apenas para lembrar como o mundo pode ser bonito."
        )

        historias.append(
            "Segundo os antigos guardiões deste livro, todo dia começa com um segredo escondido no céu. "
            f"Hoje esse segredo aparece em {temperatura:.0f} graus de temperatura, "
            f"vento vindo do {direcao_vento} e aproximadamente {nuvens:.0f} por cento de cobertura de nuvens. "
            "Quem aprende a observar o céu nunca é pego de surpresa."
        )

        historias.append(
            "Engraçado... encontrei uma anotação dizendo que certa vez um girino tentou organizar as nuvens usando uma folha como leque. "
            "Não deu muito certo. "
            f"Hoje temos {temperatura:.0f} graus, "
            f"vento soprando do {direcao_vento} a cerca de {velocidade_vento:.0f} quilômetros por hora "
            f"e uma umidade de {umidade:.0f} por cento. "
            "Parece que, desta vez, a natureza resolveu cuidar do céu sozinha."
        )

        historias.append(
            "Este capítulo começa dizendo que o céu gosta de conversar com quem sabe escutar. "
            f"Hoje ele fala através de uma temperatura de {temperatura:.0f} graus, "
            f"um vento vindo do {direcao_vento} e um céu coberto por {nuvens:.0f} por cento de nuvens. "
            "Cada página deste livro parece guardar uma pequena conversa entre a terra e o céu."
        )

        historias.append(
            "Há uma nota curiosa escrita na margem desta página. "
            "Ela diz que, antes de sair para caçar insetos, vale sempre a pena observar o clima. "
            f"Neste momento o termômetro marca {temperatura:.0f} graus, "
            f"a umidade está em {umidade:.0f} por cento "
            f"e o vento sopra pelo {direcao_vento}. "
            "Conselhos simples costumam envelhecer muito bem."
        )

        historias.append(
            "Este livro nunca repete exatamente a mesma história. "
            f"Hoje ele conta sobre um lago com {temperatura:.0f} graus, "
            f"vento vindo do {direcao_vento} e um céu ocupado por {nuvens:.0f} por cento de nuvens. "
            "Cada dia escreve uma previsão diferente, mas todos terminam lembrando que a natureza está sempre mudando."
        )

        historias.append(
            "Hum... esta parece ser uma das páginas mais antigas do livro. "
            "A tinta já está um pouco apagada, mas ainda consigo ler que "
            f"a temperatura chegou a {temperatura:.0f} graus. "
            f"O vento sopra do {direcao_vento} enquanto o céu permanece com {nuvens:.0f} por cento de nuvens. "
            "Mesmo depois de tantos anos, estas páginas continuam contando boas histórias."
        )

        historias.append(
            "Que interessante... esta página diz que cada estação possui sua própria personalidade. "
            f"Hoje ela se apresenta com {temperatura:.0f} graus, "
            f"umidade em {umidade:.0f} por cento "
            f"e vento vindo do {direcao_vento}. "
            "Talvez o céu esteja apenas esperando alguém prestar atenção antes de revelar o próximo capítulo."
        )

        extras = []

        extras_temperatura = []
        if temperatura <= 10:
            extras_temperatura = [
                "Até as pedras do lago parecem estar tremendo de frio.",
                "Nem as libélulas parecem animadas a levantar voo.",
                "Um bom dia para procurar um raio de sol.",
            ]
        elif temperatura <= 18:
            extras_temperatura = [
                "O clima está fresco, perfeito para passar horas lendo.",
                "Até respirar parece mais agradável hoje.",
                "Os antigos sapos chamariam isso de um clima acolhedor.",
            ]
        elif temperatura >= 32:
            extras_temperatura = [
                "Está tão quente que até as libélulas parecem procurar um cantinho de sombra.",
                "As pedras ao redor do lago já estão quase boas para uma soneca ao sol.",
                "Nem o vento parece ter coragem de passear por muito tempo debaixo desse calor.",
                "Hoje o lago resolveu servir um banho morninho para quem se aventurar por suas águas.",
                "Até os sapos mais animados preferem economizar alguns pulos em dias assim.",
                "O calor faz até os grilos diminuírem o ritmo de sua cantoria.",
                "As folhas parecem balançar bem devagar, como se também estivessem tentando escapar do calor.",
                "Parece um ótimo dia para encontrar uma sombra generosa e apreciar a paisagem.",
                "O sol está trabalhando horas extras hoje.",
                "Até os vaga-lumes devem estar esperando o anoitecer com um pouco mais de ansiedade.",
                "Com um calor desses, um mergulho no lago parece uma excelente ideia.",
                "As margens do lago estão tão aquecidas que caminhar descalço exige coragem.",
                "Nem as nuvens parecem querer enfrentar esse sol de frente.",
                "O velho livro recomenda bastante água e um bom descanso à sombra das árvores.",
                "Hoje até uma pedra faria inveja por conseguir ficar parada na sombra.",
            ]

        if extras_temperatura:
            extras.append(random.choice(extras_temperatura))

        if umidade >= 90:
            extras.append("As páginas quase precisam de um guarda-chuva.")
        elif umidade >= 75:
            extras.append("O ar está bastante úmido hoje.")

        if velocidade_vento >= 30:
            extras.append(
                "O vento está forte o bastante para virar as páginas sozinho."
            )
        elif velocidade_vento >= 15:
            extras.append("Uma brisa agradável acompanha a leitura.")

        if previsao_nuvens >= 80:
            extras.append(
                "O livro recomenda preparar uma boa folha para se proteger da chuva."
            )
        elif previsao_nuvens >= 60:
            extras.append("As nuvens parecem conspirar para esconder o sol.")
        elif previsao_nuvens <= 20:
            extras.append("O céu deve permanecer bastante aberto nas próximas horas.")

        if previsao_nuvens > nuvens:
            extras.append(
                "As nuvens parecem estar aumentando. Acho que o céu ainda tem novidades para hoje."
            )
        elif previsao_nuvens < nuvens:
            extras.append(
                "As nuvens começam a se dispersar. Talvez o sol resolva aparecer mais tarde."
            )

        texto = random.choice(historias)
        if extras:
            texto += "\n\n" + "\n".join(extras)

        texto += "\n\n" + random.choice(
            [
                "Vou fechar este livro antes que o vento resolva estudar meteorologia também.",
                "Estas páginas nunca deixam de me surpreender.",
                "A natureza escreve um capítulo novo todos os dias.",
                "Acho que este livro gosta mais de nuvens do que eu.",
                "Talvez amanhã o céu conte outra história.",
                "Bem... hora de guardar este livro antes que alguma rã queira pegá-lo emprestado.",
                "Curioso... este livro parece saber mais sobre o céu do que muitos meteorologistas.",
                "Cada leitura revela um detalhe diferente da natureza.",
                "O lago sempre encontra um jeito de transformar previsão em poesia.",
                "Fim da leitura... por enquanto.",
            ]
        )

        return texto

    def gerar_pagina(self, clima):
        direcao_vento = self.obter_direcao_vento(clima.wind_direction)

        # ==========================
        # ESCOLHE CATEGORIA
        # ==========================

        categorias = []
        if clima.cloudiness >= 70:
            categorias.append("chuva")
        if clima.temperature <= 15:
            categorias.append("frio")
        if clima.humidity >= 80:
            categorias.append("umidade")
        if clima.wind_speed >= 20:
            categorias.append("vento")
        if not categorias:
            categorias.append("sol")

        categoria = random.choice(categorias)

        # ==========================
        # TEXTO ESQUERDA
        # ==========================

        texto = random.choice(self.frases[categoria])

        linhas_processadas = []
        for linha in texto["linhas"]:
            linhas_processadas.append(linha.replace("{direcao}", direcao_vento))

        # ==========================
        # RETORNO
        # ==========================
        pagina_direita = self.gerar_previsao_nuvens(clima)

        return {
            "pagina_esquerda": {
                "titulo": texto["titulo"],
                "linhas": linhas_processadas,
            },
            "pagina_direita": pagina_direita,
        }

    def obter_direcao_vento(self, graus):
        direcoes = [
            "norte",
            "nordeste",
            "leste",
            "sudeste",
            "sul",
            "sudoeste",
            "oeste",
            "noroeste",
        ]

        indice = round(graus / 45) % 8

        return direcoes[indice]

    def gerar_previsao_nuvens(self, clima):
        agora = clima.cloudiness
        h1 = clima.future_cloudiness_1h
        h2 = clima.future_cloudiness_2h
        h3 = clima.future_cloudiness_3h

        tendencia = h3 - agora

        if tendencia >= 30:
            titulo = "As Nuvens Crescem"

            linhas = [
                "A presença das nuvens aumentará nas próximas horas.",
                "",
                f"Céu coberto agora: {agora:.0f}%",
                f"Em 1 hora: {h1:.0f}%",
                f"Em 2 horas: {h2:.0f}%",
                "",
                "Talvez a chuva esteja apenas esperando o momento certo para chegar.",
            ]

        elif tendencia <= -30:
            titulo = "O Céu se Abrirá"

            linhas = [
                "As nuvens perderão espaço ao longo das próximas horas.",
                "",
                f"Céu coberto agora: {agora:.0f}%",
                f"Em 1 hora: {h1:.0f}%",
                f"Em 2 horas: {h2:.0f}%",
                "",
                "A luz encontrará espaço para atravessar o céu novamente.",
            ]

        else:
            titulo = "Poucas Mudanças"

            linhas = [
                "A quantidade de nuvens mudará muito pouco.",
                "",
                f"Céu coberto agora: {agora:.0f}%",
                f"Em 1 hora: {h1:.0f}%",
                f"Em 2 horas: {h2:.0f}%",
                "",
                "Nem toda previsão fala de mudanças.",
                "Às vezes ela fala de paz.",
            ]

        return {"titulo": titulo, "linhas": linhas}
