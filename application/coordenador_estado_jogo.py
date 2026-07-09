from application.usecases import (
    AcoplarViolaoUseCase,
    AtualizarFluxoViolaoUseCase,
    ComerEsferaUseCase,
    ControlarComportamentoDuendeUseCase,
    ControlarSonoDuendeUseCase,
    DesacoplarViolaoUseCase,
    EsconderAtrasViolaoUseCase,
    ProcessarComandoSpotifyUseCase,
    ResgatarLivroUseCase,
    ResgatarViolaoUseCase,
)
from domains.sapudo.maquina_estado_sapo import EstadoSapo


class CoordenadorEstadoJogo:
    def __init__(
        self,
        sapo,
        duende,
        violao,
        livro,
        esferas,
        clima_service,
        frasco_climatico,
        evento_livro,
        spotify,
        audio,
    ):
        self.sapo = sapo
        self.duende = duende
        self.violao = violao
        self.livro = livro
        self.esferas = esferas
        self.clima_service = clima_service
        self.frasco_climatico = frasco_climatico
        self.evento_livro = evento_livro
        self.spotify = spotify
        self.audio = audio

        self.resgatar_violao = ResgatarViolaoUseCase(self.duende, self.violao)
        self.resgatar_livro = ResgatarLivroUseCase(self.duende, self.sapo, self.livro)
        self.controlar_sono_duende = ControlarSonoDuendeUseCase(
            self.sapo,
            self.duende,
            self.violao,
            self.clima_service,
            self.frasco_climatico.area_interna,
        )
        self.esconder_atras_violao = EsconderAtrasViolaoUseCase(
            self.duende, self.violao
        )
        self.comer_esfera = ComerEsferaUseCase(
            self.duende, self.frasco_climatico, self.esferas, self.evento_livro
        )
        self.controlar_comportamento_duende = ControlarComportamentoDuendeUseCase(
            self.duende, self.sapo, self.violao
        )

        self.acoplar_violao = AcoplarViolaoUseCase(
            self.violao, self.sapo, self.duende, self.spotify
        )
        self.desacoplar_violao = DesacoplarViolaoUseCase(
            self.violao, self.sapo, self.spotify, self.audio
        )
        self.processar_comando_spotify = ProcessarComandoSpotifyUseCase(
            self.spotify, self.desacoplar_violao
        )
        self.atualizar_fluxo_violao = AtualizarFluxoViolaoUseCase(
            self.sapo, self.violao, self.spotify, self.audio
        )

    def executar(self, dt):
        if self.duende.carregado:
            self._executar_fluxo_duende(dt)
            self._executar_fluxo_sapudo(dt)

    def _executar_fluxo_duende(self, dt):
        if (
            not self.clima_service.clima_disponivel
            or self.duende.animacoes.em_frente_ao_frasco
            or self.duende.animacoes.indo_para_frasco
            or self.duende.animacoes.descendo_para_dormir
            or self.duende.animacoes.dormindo
            or self.duende.animacoes.acordando
        ):
            self.controlar_sono_duende.executar(dt)
        elif (
            (self.violao.caindo or self.violao.fora_do_lugar)
            and not (self.violao.acoplado)
            and not (
                self.duende.animacoes.perseguindo_violao
                or self.duende.animacoes.guardando_violao
            )
        ):
            self.resgatar_violao.executar()
        elif (
            self.duende.animacoes.perseguindo_violao
            or self.duende.animacoes.guardando_violao
        ):
            self.resgatar_violao.atualizar(dt)
        elif self.livro.visivel and not (
            self.duende.animacoes.perseguindo_livro
            or self.duende.animacoes.guardando_livro
        ):
            self.resgatar_livro.executar()
        elif (
            self.duende.animacoes.perseguindo_livro
            or self.duende.animacoes.guardando_livro
        ):
            self.resgatar_livro.atualizar(dt)
        elif self.duende.animacoes.estado == self.duende.animacoes.INDO_ATRAS_VIOLAO:
            self.esconder_atras_violao.executar()
        elif (
            self.duende.animacoes.estado
            == self.duende.animacoes.ESCONDENDO_ATRAS_VIOLAO
        ):
            self.esconder_atras_violao.atualizar(dt)
        elif self.duende.animacoes.estado == self.duende.animacoes.INDO_ATRAS_ESFERA:
            self.comer_esfera.executar()
        elif (
            self.duende.animacoes.estado == self.duende.animacoes.PERSEGUINDO_ESFERA
            or self.duende.animacoes.estado == self.duende.animacoes.COMENDO_ESFERA
        ):
            self.comer_esfera.atualizar(dt)
        elif not self.duende.movimento_bloqueado and not self.duende.teleporte.ativo:
            self.controlar_comportamento_duende.executar(dt)

    def _executar_fluxo_sapudo(self, dt):
        if self.violao.acoplado or self.sapo.animacoes.maquina.eh(
            EstadoSapo.CHEGOU_AO_VIOLAO
        ):
            self.atualizar_fluxo_violao.executar(dt)

    def executar_comando_spotify(self, rota, finalizar_comando):
        self.processar_comando_spotify.executar(rota["dados"], finalizar_comando)

    def processar_toque_down(self, pos_virtual, renderer_violao):
        if self.desacoplar_violao.executar(
            mouse_pos=pos_virtual,
            iniciar_arraste=True,
        ):
            return

        if self.duende.processar_toque_down(pos_virtual):
            return

        # violao_rect
        if renderer_violao.obter_rect(self.violao).collidepoint(pos_virtual):
            self.violao.iniciar_arraste(*pos_virtual)
            return

    def processar_toque_up(self):
        if self.duende.arraste.ativo:
            duende_indo_dormir = self.controlar_sono_duende.processar_soltou_duende(
                self.duende.arraste,
            )

            if duende_indo_dormir:
                return

        violao_acoplado = self.acoplar_violao.executar(self.sapo.area_violao())

        if violao_acoplado:
            return
