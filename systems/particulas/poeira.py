import math

import kivy_adapter
import random
from systems.fisica import sistema_fisica

class ParticulaPoeira:

    def __init__(
        self,
        area_particulas,
        area_protegida
    ):
        
        self.area_particulas = area_particulas
        self.area_protegida = area_protegida
        self.protegido = False
        self.just_exited_timer = 0.0
        self.ativa = True
        self.resetar()

    def resetar(self):
        if self.area_protegida is not None:
            self.x = random.randint(
                self.area_protegida.left + 4,
                self.area_protegida.right - 20
            )

            self.y = random.randint(
                self.area_protegida.bottom - 57,
                self.area_protegida.bottom - 15
            )

            self.x_inicial = self.x

            self.oscilacao = random.uniform(
                0.0,
                6.28
            )

            self.tempo_vida = 0.0

            self.amplitude_lateral = random.uniform(
                2.0,
                6.0
            )

        else:
            self.x = random.randint(
                self.area_particulas.left,
                self.area_particulas.right
            )

            self.y = random.randint(
                self.area_particulas.top,
                self.area_particulas.bottom
            )

        # valores originais eram por-frame; converter para pixels/segundo
        self.vel_x = random.uniform(
            -0.08,
            0.12
        ) * 60.0

        self.vel_y = random.uniform(
            -0.03,
            -0.12
        ) * 60.0

        self.gravidade = 12.0
        self.sustentacao_restante = 0.0
        self.no_chao = False

        self.limite_chao = (
            self.area_particulas.bottom
        ) 

        self.raio = random.randint(4, 5)

        # tornar partículas um pouco menos transparentes
        self.alpha = random.randint(100, 200)

        # marca se está protegido inicialmente (ex.: dentro do pote)
        # reset entry_x whenever particle is re-spawned
        self.just_exited_timer = 0.0
        self.saiu_do_pote = False

        if self.area_protegida is not None:
            self.protegido = self.area_protegida.collidepoint(int(self.x), int(self.y))
        else:
            self.protegido = False

    def atualizar(
        self,
        ambiente,
        dt
    ):
        if not self.ativa:
            return
        
        self.tempo_vida += dt
        current_protegido = False

        if self.area_protegida is not None:
            if self.saiu_do_pote:
                current_protegido = False

            else:
                current_protegido = self.area_protegida.collidepoint(
                    int(self.x),
                    int(self.y)
                )

        # Ajustar sensibilidade ao vento de acordo com o tamanho (raio)
        # Partículas maiores sofrem menos influência do vento.
        sensibilidade = 1.0 / max(self.raio, 1)
        sensibilidade = max(0.15, min(0.6, sensibilidade))

        # Entrando no frasco: travar X e zerar velocidade horizontal
        if current_protegido and not self.protegido:
            self.vel_x = 0.0

        # Saindo do frasco: liberar e aplicar pequeno impulso na direção do vento
        if self.protegido and not current_protegido:
            self.saiu_do_pote = True

            self.vel_x = (
                ambiente.vento
                * 60.0
                * sensibilidade
            )

            self.just_exited_timer = 0.60

        # atualizar estado protegido
        self.protegido = current_protegido

        if self.protegido:
            centro_pote = (
                self.area_protegida.centerx
            )

            progresso = (
                (
                    self.area_protegida.bottom
                    - self.y
                )
                / self.area_protegida.height
            )

            progresso = max(
                0.0,
                min(1.0, progresso)
            )

            desvio_inicial = (
                self.x_inicial
                - centro_pote
            )

            self.x = (
                self.x_inicial
                - desvio_inicial * progresso
            )

            self.x += (
                math.sin(
                    self.tempo_vida * 1.5
                    + self.oscilacao
                )
                * self.amplitude_lateral
            )

            self.y += (
                self.vel_y * dt
            )

        else:
            sistema_fisica.aplicar_gravidade_simples(
                self,
                dt,
                0.5
            )

            wind_accel = (
                ambiente.vento
                * 60.0
                * sensibilidade
            )

            target_vx = (
                ambiente.vento
                * 60.0
                * sensibilidade
            )

            self.vel_x += (
                target_vx
                - self.vel_x
            ) * 0.25 * dt

            if self.just_exited_timer > 0:
                wind_accel *= 6.0

            self.vel_x += (
                wind_accel
                * dt
            )

            self.vel_x *= 0.998

            # limitar velocidade para evitar deriva numérica ao longo do tempo
            max_v = 10.0
            if self.vel_x > max_v:
                self.vel_x = max_v
            elif self.vel_x < -max_v:
                self.vel_x = -max_v

            # integrar posição usando dt
            self.x += self.vel_x * dt
            self.y += self.vel_y * dt

            # reduzir timer de pós-saída
            if getattr(self, 'just_exited_timer', 0.0) > 0.0:
                self.just_exited_timer = max(0.0, self.just_exited_timer - dt)

            margem = 150

            if (
                self.x < self.area_particulas.left - margem
                or self.x > self.area_particulas.right + margem
                or self.y < self.area_particulas.top - margem
                or self.y > self.area_particulas.bottom + margem
            ):
                self.resetar()
                return

    def desenhar(
        self,
        tela
    ):
        if not self.ativa:
            return

        tamanho = self.raio * 6

        superficie = kivy_adapter.Surface(
            (
                tamanho,
                tamanho
            ),
            kivy_adapter.SRCALPHA
        )

        centro = tamanho // 2

        # =================================
        # GLOW EXTERNO
        # =================================

        kivy_adapter.draw.circle(
            superficie,
            (
                255,
                255,
                255,
                int(self.alpha * 0.25)
            ),
            (
                centro,
                centro
            ),
            self.raio * 2
        )

        # =================================
        # NÚCLEO
        # =================================

        kivy_adapter.draw.circle(
            superficie,
            (
                255,
                255,
                255,
                self.alpha
            ),
            (
                centro,
                centro
            ),
            self.raio
        )

        tela.blit(
            superficie,
            (
                self.x,
                self.y
            )
        )

    def obter_rect(self):

        tamanho = self.raio * 6

        return kivy_adapter.Rect(
            self.x,
            self.y,
            tamanho,
            tamanho
        )