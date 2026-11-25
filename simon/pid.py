"""Controladores PID e parâmetros ajustáveis do robô."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PIDConfig:
    kp: float
    ki: float
    kd: float
    limite_saida: float
    limite_integral: float = 10.0


class PID:
    def __init__(self, config: PIDConfig) -> None:
        self.config = config
        self.integral = 0.0
        self.medida_anterior: float | None = None

    def resetar(self) -> None:
        self.integral = 0.0
        self.medida_anterior = None

    def atualizar(self, alvo: float, medida: float, dt: float) -> float:
        if dt <= 0.0:
            return 0.0

        erro = alvo - medida
        integral_candidata = self.integral + erro * dt
        integral_candidata = max(
            -self.config.limite_integral,
            min(self.config.limite_integral, integral_candidata),
        )
        derivada = (
            0.0
            if self.medida_anterior is None
            else -(medida - self.medida_anterior) / dt
        )
        self.medida_anterior = medida

        saida_sem_limite = (
            self.config.kp * erro
            + self.config.ki * integral_candidata
            + self.config.kd * derivada
        )
        saida = max(
            -self.config.limite_saida,
            min(self.config.limite_saida, saida_sem_limite),
        )
        if saida == saida_sem_limite or erro * saida_sem_limite < 0.0:
            self.integral = integral_candidata
        return saida


class ControleSegway:
    """Controla a tração e corrige a inclinação do robô."""

    def __init__(self) -> None:
        self.pid_velocidade = PID(
            #PIDConfig(kp=10.0, ki=1.0, kd=0.0, limite_saida=40.0)
            PIDConfig(kp=10.0, ki=1.0, kd=0.0, limite_saida=40.0)
        )
        self.pid_inclinacao = PID(
            #PIDConfig(kp=35.0, ki=0.0, kd=12.0, limite_saida=45.0)
            PIDConfig(kp=15.0, ki=0.0, kd=5.0, limite_saida=20.0)
        )

    def resetar(self) -> None:
        self.pid_velocidade.resetar()
        self.pid_inclinacao.resetar()

    def atualizar(
        self, velocidade_alvo: float, inclinacao: float, velocidade: float, dt: float
    ) -> tuple[float, float]:
        forca = self.pid_velocidade.atualizar(
            velocidade_alvo, velocidade, dt
        )
        correcao_inclinacao = self.pid_inclinacao.atualizar(
            0.0, inclinacao, dt
        )
        return forca, correcao_inclinacao