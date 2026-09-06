from application.usecases.cobra.atacar import AtacarCobraUseCase


class AtacarUrsoUseCase(AtacarCobraUseCase):
    """Combate especial do urso que surge da caverna à noite."""

    # O urso é mais pesado e não precisa encostar tanto no alvo.
    DISTANCIA_PARADA = 68

    def iniciar_ataque_noturno(self, urso):
        """Inicia a investida noturna sem antecipar a orientação pelo alvo.

        A orientação durante a perseguição deve ser determinada pelo deslocamento
        real de cada trecho da rota. O Sapudo define o alvo da perseguição, não
        o lado para o qual o Urso deve olhar antes de começar a se mover.
        """
        flip_anterior = getattr(getattr(urso, "animacoes", None), "flip", False)
        sapudo = getattr(self.cenario_principal, "sapudo", None)
        if sapudo is None or getattr(sapudo, "vida", 0) <= 0:
            sapudo = next(
                (
                    personagem
                    for personagem in getattr(self.cenario_principal, "personagens", ())
                    if getattr(personagem, "nome", None) == "sapudo"
                    and getattr(personagem, "vida", 0) > 0
                ),
                None,
            )

        if sapudo is None:
            return False

        self.iniciar(sapudo, urso)
        # ``iniciar`` do combate pode orientar pelo alvo imediatamente. Para a
        # perseguição do Urso isso ainda é prematuro: o primeiro trecho pode ser
        # vertical ou contornar um obstáculo. Preserve a orientação anterior e
        # deixe MoverPersonagemUseCase atualizá-la conforme o deslocamento real.
        if hasattr(urso, "animacoes") and hasattr(urso.animacoes, "definir_flip"):
            urso.animacoes.definir_flip(flip_anterior)
        return True

    def tentar_adquirir_inimigo_proximo(self, personagem):
        # O urso não escolhe outros alvos por conta própria. A investida é
        # sempre iniciada explicitamente pela rotina noturna.
        return False
