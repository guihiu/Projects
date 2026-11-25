"""Modelo físico simplificado de um robô autoequilibrado de duas rodas."""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class ParametrosFisicos:
    massa_rodas: float = 3.0
    massa_corpo: float = 8.0
    comprimento_pendulo: float = 0.58
    gravidade: float = 9.81
    atrito_deslocamento: float = 1.4
    amortecimento_inclinacao: float = 0.08
    forca_maxima: float = 75.0
    aceleracao_direcao: float = 3.5
    amortecimento_direcao: float = 1.8
    velocidade_direcao_maxima: float = 2.2


class RoboSegway:
    """Estado e integração da física; ângulos são medidos em radianos."""

    def __init__(self, parametros: ParametrosFisicos | None = None) -> None:
        self.parametros = parametros or ParametrosFisicos()
        self.resetar()

    def resetar(self) -> None:
        self.x = 0.0
        self.z = 0.0
        self.yaw = 0.0
        self.velocidade = 0.0
        self.inclinacao = 0.0
        self.velocidade_inclinacao = 0.0
        self.velocidade_direcao = 0.0

    def atualizar(
        self,
        dt: float,
        forca: float,
        direcao: float,
        correcao_inclinacao: float = 0.0,
    ) -> None:
        """Avança a física com força motriz e correção angular do controlador."""
        if dt <= 0.0:
            return

        p = self.parametros
        massa_total = p.massa_rodas + p.massa_corpo
        seno = math.sin(self.inclinacao)
        cosseno = math.cos(self.inclinacao)
        denominador = massa_total - p.massa_corpo * cosseno**2
        forca_motor = max(-p.forca_maxima, min(p.forca_maxima, forca))
        forca_liquida = forca_motor - p.atrito_deslocamento * self.velocidade

        aceleracao = (
            forca_liquida
            + p.massa_corpo
            * p.comprimento_pendulo
            * self.velocidade_inclinacao**2
            * seno
            - p.massa_corpo * p.gravidade * seno * cosseno
        ) / denominador
        aceleracao_inclinacao = (
            p.gravidade * seno - aceleracao * cosseno
        ) / p.comprimento_pendulo
        aceleracao_inclinacao += correcao_inclinacao
        aceleracao_inclinacao -= (
            p.amortecimento_inclinacao * self.velocidade_inclinacao
        )

        self.velocidade += aceleracao * dt
        self.velocidade_inclinacao += aceleracao_inclinacao * dt
        self.inclinacao += self.velocidade_inclinacao * dt

        aceleracao_direcao = (
            max(-1.0, min(1.0, direcao)) * p.aceleracao_direcao
            - p.amortecimento_direcao * self.velocidade_direcao
        )
        self.velocidade_direcao += aceleracao_direcao * dt
        self.velocidade_direcao = max(
            -p.velocidade_direcao_maxima,
            min(p.velocidade_direcao_maxima, self.velocidade_direcao),
        )
        self.yaw += self.velocidade_direcao * dt

        self.x += self.velocidade * math.sin(self.yaw) * dt
        self.z += self.velocidade * math.cos(self.yaw) * dt
