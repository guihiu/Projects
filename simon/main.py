"""Janela, entrada do teclado e câmera 3D para a simulação do Segway."""

import math
import pygame

from mecanica import RoboSegway
from pid import ControleSegway


LARGURA, ALTURA = 1100, 720
PASSO_FISICO = 1.0 / 120.0
VELOCIDADE_ALVO_MAXIMA = 2.5


class Camera:
    def __init__(self) -> None:
        self.yaw = math.radians(38)
        self.pitch = math.radians(22)
        self.distancia = 6.5

    def projetar(
        self, ponto: tuple[float, float, float], robo: RoboSegway
    ) -> tuple[int, int] | None:
        dx = ponto[0] - robo.x
        dy = ponto[1] - 0.75
        dz = ponto[2] - robo.z
        seno_yaw, cosseno_yaw = math.sin(self.yaw), math.cos(self.yaw)
        seno_pitch, cosseno_pitch = math.sin(self.pitch), math.cos(self.pitch)

        lado = dx * cosseno_yaw - dz * seno_yaw
        profundidade_relativa = dx * seno_yaw + dz * cosseno_yaw
        profundidade = (
            self.distancia
            + profundidade_relativa * cosseno_pitch
            - dy * seno_pitch
        )
        if profundidade <= 0.1:
            return None

        vertical = (
            -profundidade_relativa * seno_pitch + dy * cosseno_pitch
        )
        escala = min(LARGURA, ALTURA) * 0.92 / profundidade
        return (
            round(LARGURA / 2 + lado * escala),
            round(ALTURA / 2 - vertical * escala),
        )


def desenhar_linha_3d(
    tela: pygame.Surface,
    camera: Camera,
    robo: RoboSegway,
    pontos: list[tuple[float, float, float]],
    cor: tuple[int, int, int],
    largura: int = 1,
) -> None:
    projetados = [camera.projetar(ponto, robo) for ponto in pontos]
    if all(ponto is not None for ponto in projetados):
        pygame.draw.lines(tela, cor, False, projetados, largura)


def ponto_robo(
    robo: RoboSegway, x: float, y: float, z: float, inclinar: bool = False
) -> tuple[float, float, float]:
    if inclinar:
        altura_relativa = y - 0.2
        y = 0.2 + altura_relativa * math.cos(robo.inclinacao) - z * math.sin(
            robo.inclinacao
        )
        z = altura_relativa * math.sin(robo.inclinacao) + z * math.cos(
            robo.inclinacao
        )
    seno, cosseno = math.sin(robo.yaw), math.cos(robo.yaw)
    return (
        robo.x + x * cosseno + z * seno,
        y,
        robo.z - x * seno + z * cosseno,
    )


def desenhar_piso(tela: pygame.Surface, camera: Camera, robo: RoboSegway) -> None:
    inicio_x = math.floor(robo.x) - 6
    inicio_z = math.floor(robo.z) - 6
    fim_x, fim_z = inicio_x + 12, inicio_z + 12
    for x in range(inicio_x, fim_x + 1):
        cor = (57, 72, 81) if x % 2 else (48, 63, 72)
        desenhar_linha_3d(
            tela,
            camera,
            robo,
            [(x, 0, inicio_z), (x, 0, fim_z)],
            cor,
        )
    for z in range(inicio_z, fim_z + 1):
        cor = (57, 72, 81) if z % 2 else (48, 63, 72)
        desenhar_linha_3d(
            tela,
            camera,
            robo,
            [(inicio_x, 0, z), (fim_x, 0, z)],
            cor,
        )


def desenhar_robo(tela: pygame.Surface, camera: Camera, robo: RoboSegway) -> None:
    for x in (-0.38, 0.38):
        centro = (x, 0.2, 0.0)
        circulo_externo = [
            ponto_robo(
                robo,
                x,
                centro[1] + 0.2 * math.cos(angulo),
                centro[2] + 0.2 * math.sin(angulo),
            )
            for angulo in [i * math.tau / 32 for i in range(33)]
        ]
        projetados = [camera.projetar(ponto, robo) for ponto in circulo_externo]
        if all(ponto is not None for ponto in projetados):
            pygame.draw.lines(tela, (24, 30, 34), True, projetados, 13)
            pygame.draw.lines(tela, (93, 112, 121), True, projetados, 3)

        hub = camera.projetar(ponto_robo(robo, x, 0.2, 0.0), robo)
        if hub is not None:
            pygame.draw.circle(tela, (38, 178, 191), hub, 5)

    vertices_locais = [
        (-0.28, 0.42, -0.13),
        (0.28, 0.42, -0.13),
        (0.28, 1.36, -0.13),
        (-0.28, 1.36, -0.13),
        (-0.28, 0.42, 0.13),
        (0.28, 0.42, 0.13),
        (0.28, 1.36, 0.13),
        (-0.28, 1.36, 0.13),
    ]
    vertices = [ponto_robo(robo, *ponto, inclinar=True) for ponto in vertices_locais]
    faces = [
        ([0, 1, 2, 3], (23, 135, 153)),
        ([4, 5, 6, 7], (19, 105, 124)),
        ([0, 4, 7, 3], (28, 160, 173)),
        ([1, 5, 6, 2], (16, 87, 107)),
        ([3, 2, 6, 7], (55, 191, 195)),
        ([0, 1, 5, 4], (15, 75, 93)),
    ]
    faces_projetadas = []
    for indices, cor in faces:
        face = [camera.projetar(vertices[i], robo) for i in indices]
        if all(ponto is not None for ponto in face):
            faces_projetadas.append((sum(vertices[i][1] for i in indices), face, cor))
    for _, face, cor in sorted(faces_projetadas):
        pygame.draw.polygon(tela, cor, face)
        pygame.draw.polygon(tela, (113, 221, 218), face, 2)

    for lado in (-0.22, 0.22):
        base = ponto_robo(robo, lado, 0.46, 0.0, inclinar=True)
        topo = ponto_robo(robo, lado, 1.55, 0.0, inclinar=True)
        base_2d, topo_2d = camera.projetar(base, robo), camera.projetar(topo, robo)
        if base_2d is not None and topo_2d is not None:
            pygame.draw.line(tela, (175, 197, 200), base_2d, topo_2d, 6)
            pygame.draw.line(tela, (66, 83, 89), base_2d, topo_2d, 2)


def desenhar_hud(
    tela: pygame.Surface,
    fonte: pygame.font.Font,
    robo: RoboSegway,
    velocidade_alvo: float,
) -> None:
    painel = pygame.Surface((340, 140), pygame.SRCALPHA)
    painel.fill((8, 15, 20, 205))
    tela.blit(painel, (18, 18))
    linhas = [
        ("SEGWAY  /  SIMULAÇÃO FÍSICA", (111, 226, 221)),
        (f"Velocidade: {robo.velocidade:+.2f} m/s", (238, 242, 240)),
        (f"Alvo: {velocidade_alvo:+.2f} m/s", (178, 199, 205)),
        (f"Inclinação: {math.degrees(robo.inclinacao):+.1f}°", (238, 242, 240)),
    ]
    for indice, (texto, cor) in enumerate(linhas):
        tela.blit(fonte.render(texto, True, cor), (32, 30 + indice * 28))

    ajuda = [
        "↑ / ↓  mover      ← / →  virar",
        "Arraste o mouse  girar câmera",
        "R  reiniciar      ESC  sair",
    ]
    for indice, texto in enumerate(ajuda):
        imagem = fonte.render(texto, True, (220, 229, 229))
        tela.blit(imagem, (20, ALTURA - 84 + indice * 23))


def main() -> None:
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Simulação Segway")
    relogio = pygame.time.Clock()
    fonte = pygame.font.Font(None, 24)
    robo = RoboSegway()
    controle = ControleSegway()
    camera = Camera()
    velocidade_alvo = 0.0
    arrastando_camera = False
    acumulador = 0.0
    executando = True

    while executando:
        dt = min(relogio.tick(60) / 1000.0, 0.05)
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                executando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    executando = False
                elif evento.key == pygame.K_r:
                    robo.resetar()
                    controle.resetar()
                    velocidade_alvo = 0.0
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:
                    arrastando_camera = True
                elif evento.button == 4:
                    camera.distancia = max(3.0, camera.distancia - 0.5)
                elif evento.button == 5:
                    camera.distancia = min(12.0, camera.distancia + 0.5)
            elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
                arrastando_camera = False
            elif evento.type == pygame.MOUSEMOTION and arrastando_camera:
                camera.yaw -= evento.rel[0] * 0.008
                camera.pitch = max(
                    0.08, min(1.05, camera.pitch - evento.rel[1] * 0.006)
                )
            elif evento.type == pygame.MOUSEWHEEL:
                camera.distancia = max(
                    3.0, min(12.0, camera.distancia - evento.y * 0.4)
                )

        teclas = pygame.key.get_pressed()
        entrada_movimento = float(teclas[pygame.K_UP]) - float(
            teclas[pygame.K_DOWN]
        )
        entrada_direcao = float(teclas[pygame.K_LEFT]) - float(
            teclas[pygame.K_RIGHT]
        )
        velocidade_alvo = entrada_movimento * VELOCIDADE_ALVO_MAXIMA

        acumulador += dt
        while acumulador >= PASSO_FISICO:
            forca, correcao_inclinacao = controle.atualizar(
                velocidade_alvo, robo.inclinacao, robo.velocidade, PASSO_FISICO
            )
            robo.atualizar(
                PASSO_FISICO, forca, entrada_direcao, correcao_inclinacao
            )
            acumulador -= PASSO_FISICO

        tela.fill((19, 28, 35))
        desenhar_piso(tela, camera, robo)
        desenhar_robo(tela, camera, robo)
        desenhar_hud(tela, fonte, robo, velocidade_alvo)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()