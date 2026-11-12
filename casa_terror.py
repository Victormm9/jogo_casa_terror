
import pygame
import sys
import random
import math

pygame.init()
# O jogo também funciona sem dispositivo de áudio disponível.
try:
    pygame.mixer.init()
except pygame.error:
    pass

LARGURA, ALTURA = 900, 600
FPS = 60

tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Casa dos Pesadelos: O Alfinete")
relogio = pygame.time.Clock()
fonte = pygame.font.SysFont("Arial", 22)
fonte_grande = pygame.font.SysFont("Arial", 48, bold=True)

# CORES
PRETO = (10, 10, 12)
CHAO = (55, 45, 40)
PAREDE_COR = (90, 85, 80)
PORTA_FECHADA = (100, 55, 30)
PORTA_ABERTA = (30, 120, 50)
BRANCO = (230, 230, 230)
AMARELO = (240, 190, 40)
VERDE = (50, 220, 50)
VERMELHO = (200, 30, 30)
CIANO = (80, 220, 220)

# ASSETS com fallback
def carregar_img(path):
    try:
        img = pygame.image.load(path)
        return pygame.transform.scale(img, (LARGURA, ALTURA))
    except:
        s = pygame.Surface((LARGURA, ALTURA))
        s.fill((180, 0, 0))
        # cara assustadora improvisada
        pygame.draw.circle(s, (255,255,255), (450, 280), 100)
        pygame.draw.circle(s, (0,0,0), (415, 260), 20)
        pygame.draw.circle(s, (0,0,0), (485, 260), 20)
        pygame.draw.ellipse(s, (0,0,0), (400, 330, 100, 60))
        return s

def carregar_som(path):
    try:
        return pygame.mixer.Sound(path)
    except:
        return None

imagem_susto = carregar_img("assets/jumpscare.png")
som_susto = carregar_som("assets/susto.wav")
som_pickup = carregar_som("assets/pickup.wav")
som_acerto = carregar_som("assets/acerto.wav")
som_erro = carregar_som("assets/erro.wav")
som_porta = carregar_som("assets/porta.wav")

def tocar(som):
    if som:
        try: som.play()
        except: pass

# MAPA
paredes = [
    pygame.Rect(100, 50, 700, 20),
    pygame.Rect(100, 50, 20, 500),
    pygame.Rect(780, 50, 20, 500),
    pygame.Rect(100, 530, 280, 20),
    pygame.Rect(480, 530, 320, 20)
]
porta = pygame.Rect(380, 530, 100, 20)

jogador = pygame.Rect(430, 280, 30, 30)
alfinete = pygame.Rect(250, 200, 30, 10)
pilhas = [pygame.Rect(150,150,20,15), pygame.Rect(700,400,20,15), pygame.Rect(420,120,20,15)]
bilhetes = [
    {"rect": pygame.Rect(650, 120, 20, 20), "texto": "DICA: Ele enxerga a luz... Apague com [F]!"},
    {"rect": pygame.Rect(200, 450, 20, 20), "texto": "DICA: Use o alfinete na porta e gire com ESPAÇO!"},
]

monstro = pygame.Rect(700, 150, 32, 32)
monstro_ativo = False
monstro_vel = 1.7

# ESTADO
estado = "menu"  # menu, jogando, puzzle, venceu, morreu
alfinete_coletado = False
bateria = 100.0
lanterna_ligada = True
estamina = 100.0
mensagem, mensagem_tempo = "", 0
jumpscare_ativo = False
jumpscare_tempo = 0
shake = 0
tempo_jogo = 0
objetivo = "Procure o alfinete na casa"

# PUZZLE lockpick - 3 fases
puzzle_etapa = 0
puzzle_pos = 0.0
puzzle_dir = 1
puzzle_vel = 0.015
zona_inicio, zona_tam = 0.3, 0.18

def nova_zona_puzzle():
    global zona_inicio, zona_tam, puzzle_vel
    zona_tam = max(0.09, 0.20 - puzzle_etapa * 0.04)
    zona_inicio = random.uniform(0.05, 0.90 - zona_tam)
    puzzle_vel = 0.012 + puzzle_etapa * 0.006

nova_zona_puzzle()

def reset():
    global alfinete_coletado, bateria, estamina, monstro_ativo, monstro_vel
    global jumpscare_ativo, puzzle_etapa, estado, mensagem, pilhas, lanterna_ligada
    global tempo_jogo, objetivo, mensagem_tempo, shake, puzzle_pos, puzzle_dir
    jogador.topleft = (430, 280)
    pilhas = [
        pygame.Rect(150, 150, 20, 15),
        pygame.Rect(700, 400, 20, 15),
        pygame.Rect(420, 120, 20, 15)
    ]
    monstro.topleft = (700, 150)
    alfinete_coletado = False
    bateria, estamina = 100.0, 100.0
    lanterna_ligada = True
    monstro_ativo = False
    monstro_vel = 1.7
    jumpscare_ativo = False
    puzzle_etapa = 0
    puzzle_pos = 0.0
    puzzle_dir = 1
    shake = 0
    tempo_jogo = 0
    objetivo = "Procure o alfinete na casa"
    mensagem = ""
    mensagem_tempo = 0
    nova_zona_puzzle()
    estado = "jogando"

def mover_com_colisao(r, dx, dy, blocos):
    r.x += dx
    for b in blocos:
        if r.colliderect(b):
            r.x = b.left - r.width if dx > 0 else b.right if dx < 0 else r.x
    r.y += dy
    for b in blocos:
        if r.colliderect(b):
            r.y = b.top - r.height if dy > 0 else b.bottom if dy < 0 else r.y

def mostrar_msg(txt, dur=2400):
    global mensagem, mensagem_tempo
    mensagem = txt
    mensagem_tempo = pygame.time.get_ticks() + dur


def atualizar_objetivo():
    global objetivo
    if not alfinete_coletado:
        objetivo = "Procure o alfinete na casa"
    elif estado == "jogando":
        objetivo = "Volte até a porta e use [E]"
    elif estado == "puzzle":
        objetivo = "Alinhe a área verde e aperte ESPAÇO"
    elif estado == "venceu":
        objetivo = "Você escapou da casa"
    elif estado == "morreu":
        objetivo = "O monstro te alcançou"

# LOOP
while True:
    dt = relogio.tick(FPS)
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit(); sys.exit()

        if evento.type == pygame.KEYDOWN:
            if estado == "menu" and evento.key == pygame.K_RETURN:
                reset()
            elif estado in ("venceu", "morreu") and evento.key == pygame.K_r:
                reset()
            elif estado == "jogando":
                if evento.key == pygame.K_f:
                    if bateria <= 0:
                        mostrar_msg("Bateria vazia! Ache uma pilha.", 1800)
                    else:
                        lanterna_ligada = not lanterna_ligada
                        tocar(som_pickup)
                        mostrar_msg("Lanterna " + ("ligada" if lanterna_ligada else "apagada"), 1200)
                if evento.key == pygame.K_e:
                    area = jogador.inflate(70, 70)
                    # 1. pegar alfinete
                    if not alfinete_coletado and area.colliderect(alfinete):
                        alfinete_coletado = True
                        tocar(som_pickup)
                        mostrar_msg("Você pegou um ALFINETE! Vá até a porta!")
                    # 2. pegar pilha
                    for p in pilhas[:]:
                        if area.colliderect(p):
                            pilhas.remove(p)
                            bateria = min(100, bateria + 40)
                            tocar(som_pickup)
                            mostrar_msg("Pilha coletada! +40% bateria")
                            break
                    # 3. ler bilhete
                    for b in bilhetes:
                        if area.colliderect(b["rect"]):
                            mostrar_msg(b["texto"], 4000)
                    # 4. abrir puzzle na porta
                    if alfinete_coletado and area.colliderect(porta):
                        estado = "puzzle"
                        puzzle_etapa = 0
                        nova_zona_puzzle()
                        tocar(som_pickup)
                        mostrar_msg("TRAVA DA PORTA - alinhe a zona verde!", 2200)
            elif estado == "puzzle":
                if evento.key == pygame.K_ESCAPE:
                    estado = "jogando"
                    mostrar_msg("Você saiu do mini-game.", 1400)
                if evento.key == pygame.K_SPACE:
                    # acertou?
                    fim = zona_inicio + zona_tam
                    if zona_inicio <= puzzle_pos <= fim:
                        tocar(som_acerto)
                        puzzle_etapa += 1
                        if puzzle_etapa >= 3:
                            tocar(som_porta)
                            estado = "venceu"
                            mostrar_msg("A porta abriu! Você escapou!", 2500)
                        else:
                            puzzle_pos = 0
                            nova_zona_puzzle()
                            mostrar_msg(f"Parabéns! Trava {puzzle_etapa}/3", 1800)
                    else:
                        tocar(som_erro)
                        monstro_vel += 0.25  # errou faz barulho!
                        puzzle_etapa = 0
                        nova_zona_puzzle()
                        mostrar_msg("ERROU! Ele ouviu você...", 2000)

    # ===== UPDATE =====
    if estado == "jogando":
        tempo_jogo += dt
        teclas = pygame.key.get_pressed()
        correndo = (teclas[pygame.K_LSHIFT] or teclas[pygame.K_RSHIFT]) and estamina > 1
        vel = 6 if correndo else 4

        dx = ((teclas[pygame.K_d] or teclas[pygame.K_RIGHT]) - (teclas[pygame.K_a] or teclas[pygame.K_LEFT])) * vel
        dy = ((teclas[pygame.K_s] or teclas[pygame.K_DOWN]) - (teclas[pygame.K_w] or teclas[pygame.K_UP])) * vel
        if dx and dy:
            dx, dy = int(dx*0.71), int(dy*0.71)
        if correndo and (dx or dy):
            estamina = max(0, estamina - 0.5)
        else:
            estamina = min(100, estamina + 0.3)

        blocos = paredes if alfinete_coletado else paredes + [porta]
        mover_com_colisao(jogador, dx, dy, blocos)

        if lanterna_ligada and bateria > 0:
            bateria -= 0.02
            bateria = max(0, bateria)
            if bateria <= 0:
                lanterna_ligada = False
                mostrar_msg("Bateria esgotada! Use a lanterna com cautela.", 1800)

        # JUMPSCARE uma vez perto do alfinete
        if not monstro_ativo and not alfinete_coletado:
            if jogador.inflate(130,130).colliderect(alfinete):
                jumpscare_ativo = True
                jumpscare_tempo = pygame.time.get_ticks()
                monstro_ativo = True
                shake = 20
                tocar(som_susto)

        # MONSTRO persegue
        if monstro_ativo:
            dist = math.hypot(jogador.centerx-monstro.centerx, jogador.centery-monstro.centery)
            visao = 380 if lanterna_ligada and bateria > 0 else 180
            if dist < visao:
                # perseguir
                ang = math.atan2(jogador.centery-monstro.centery, jogador.centerx-monstro.centerx)
                mx = round(math.cos(ang) * monstro_vel)
                my = round(math.sin(ang) * monstro_vel)
                if mx == 0 and abs(math.cos(ang)) > 0.1:
                    mx = 1 if math.cos(ang) > 0 else -1
                if my == 0 and abs(math.sin(ang)) > 0.1:
                    my = 1 if math.sin(ang) > 0 else -1
                mover_com_colisao(monstro, mx, my, paredes)
            else:
                # vagar
                if random.random() < 0.02:
                    mx, my = random.choice([(1,0),(-1,0),(0,1),(0,-1)])
                    mover_com_colisao(monstro, mx*2, my*2, paredes)

            if monstro.colliderect(jogador):
                estado = "morreu"
                tocar(som_susto)
                mostrar_msg("ELE TE PEGOU! Pressione R para recomeçar.", 4000)

        atualizar_objetivo()

    if estado == "puzzle":
        puzzle_pos += puzzle_dir * puzzle_vel * (dt/16.6)
        if puzzle_pos > 1:
            puzzle_pos, puzzle_dir = 1, -1
        if puzzle_pos < 0:
            puzzle_pos, puzzle_dir = 0, 1

    atualizar_objetivo()

    # ===== DESENHO =====
    tela.fill(PRETO)
    ox, oy = 0, 0
    if shake > 0 or jumpscare_ativo:
        ox, oy = random.randint(-8,8), random.randint(-8,8)
        shake = max(0, shake-1)

    if estado == "menu":
        t = fonte_grande.render("CASA DOS PESADELOS", True, VERMELHO)
        s = fonte.render("Ache o ALFINETE, fuja do MONSTRO, arrombe a porta.", True, BRANCO)
        c = fonte.render("WASD move | SHIFT corre | F lanterna | E pega | ENTER começa", True, CIANO)
        tela.blit(t, (200, 200)); tela.blit(s, (180, 280)); tela.blit(c, (120, 330))

    elif estado in ("venceu", "morreu"):
        cor = VERDE if estado=="venceu" else VERMELHO
        txt = "VOCE ESCAPOU!" if estado=="venceu" else "ELE TE PEGOU!"
        t = fonte_grande.render(txt, True, cor)
        r = fonte.render("Pressione R para jogar de novo", True, BRANCO)
        tela.blit(t, (280, 250)); tela.blit(r, (280, 320))

    else:
        # chao + paredes com offset shake
        pygame.draw.rect(tela, CHAO, (120+ox, 70+oy, 660, 460))
        for p in paredes:
            pygame.draw.rect(tela, PAREDE_COR, p.move(ox,oy))
        pygame.draw.rect(tela, PORTA_ABERTA if alfinete_coletado else PORTA_FECHADA, porta.move(ox,oy))

        # alfinete desenhado como agulha
        if not alfinete_coletado:
            cx, cy = alfinete.centerx+ox, alfinete.centery+oy
            pygame.draw.line(tela, (200,200,210), (cx-15,cy), (cx+15,cy), 3)
            pygame.draw.circle(tela, (180,180,190), (cx+15, cy), 5)
            pygame.draw.circle(tela, PRETO, (cx+15, cy), 2)
            # brilho pulsante
            br = int(150 + 100*abs(math.sin(pygame.time.get_ticks()/300)))
            pygame.draw.circle(tela, (br,br,120), (cx,cy), 4)

        for p in pilhas:
            r = p.move(ox,oy)
            pygame.draw.rect(tela, VERDE, r)
            pygame.draw.rect(tela, BRANCO, r, 1)
            pygame.draw.line(tela, BRANCO, (r.centerx, r.top+2), (r.centerx, r.top+5), 2)

        for b in bilhetes:
            pygame.draw.rect(tela, (220,220,200), b["rect"].move(ox,oy))

        # monstro
        if monstro_ativo:
            m = monstro.move(ox,oy)
            pygame.draw.rect(tela, (40,0,0), m)
            pygame.draw.circle(tela, VERMELHO, (m.centerx-6, m.centery-5), 4)
            pygame.draw.circle(tela, VERMELHO, (m.centerx+6, m.centery-5), 4)

        pygame.draw.rect(tela, BRANCO, jogador.move(ox,oy))

        # escuridão + lanterna tremendo se bateria baixa
        esc = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        esc.fill((0,0,0,240))
        if lanterna_ligada and bateria > 0:
            raio = 130
            if bateria < 25:
                raio += random.randint(-15, 10)  # tremendo!
            pygame.draw.circle(esc, (0,0,0,0), (jogador.centerx+ox, jogador.centery+oy), raio)
        tela.blit(esc, (0,0))

        # HUD
        tela.blit(fonte.render(f"Bateria: {int(bateria)}%  Estamina: {int(estamina)}%", True, BRANCO), (20,15))
        pygame.draw.rect(tela, (80,80,80), (280,20,100,15))
        pygame.draw.rect(tela, (50,220,50), (280,20,int(bateria),15))
        obj = objetivo
        if monstro_ativo and estado == "jogando":
            obj += " | O monstro te viu!"
        tela.blit(fonte.render(obj, True, AMARELO), (20,570))

        if mensagem and pygame.time.get_ticks() < mensagem_tempo:
            tela.blit(fonte.render(mensagem, True, CIANO), (20, 45))

        # OVERLAY PUZZLE
        if estado == "puzzle":
            pygame.draw.rect(tela, (0,0,0,200), (0,0,LARGURA,ALTURA))
            tela.blit(fonte_grande.render(f"ARROMBAR {puzzle_etapa+1}/3", True, BRANCO), (300,150))
            tela.blit(fonte.render("Aperte ESPAÇO na área VERDE! ESC cancela", True, CIANO), (240,210))
            bx, bw, by, bh = 200, 500, 300, 30
            pygame.draw.rect(tela, (60,60,60), (bx,by,bw,bh))
            pygame.draw.rect(tela, VERDE, (bx+zona_inicio*bw, by, zona_tam*bw, bh))
            px = bx + puzzle_pos*bw
            pygame.draw.rect(tela, BRANCO, (px-3, by-10, 6, bh+20))

        # JUMPSCARE 1.5s
        if jumpscare_ativo:
            if pygame.time.get_ticks() - jumpscare_tempo < 1500:
                tela.blit(imagem_susto, (0,0))
            else:
                jumpscare_ativo = False

    pygame.display.flip()