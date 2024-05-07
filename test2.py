import pygame
import sys
import time
import random
#import colordaass
#saaaa
staticmethod
# Definir coloress
BLANCO, NEGRO, GRIS, ROJO, AZUL = (255, 255, 255), (0, 0, 0), (128, 128, 128), (255, 0, 0), (0, 0, 255)
NORTE, SUR, ESTE, OESTE = 0, 1, 2, 3

# Funciones del modelo de Markov
def mapear_a_estados(mapa):
    estados = []
    for i in range(len(mapa)):
        for j in range(len(mapa[0])):
            if mapa[i][j] not in "_M":
                estados.append((i, j))
    return estados

def construir_matriz_transicion(mapa, estados, direccion_principal):
    n = len(estados)
    P = [[0 for _ in range(n)] for _ in range(n)]
    
    def indice_estado(estado):
        if estado in estados:
            return estados.index(estado)
        return None
    
    for estado in estados:
        i, j = estado
        indice_actual = indice_estado((i, j))
        P[indice_actual][indice_actual] = 1.0

        # Definir direcciones y probabilidades dentro del bucle
        desplazamientos_direccion = {
            'norte': ((i-1, j), 0.90, [('este', (i, j+1), 0.05), ('oeste', (i, j-1), 0.05)]),
            'sur':   ((i+1, j), 0.90, [('este', (i, j+1), 0.05), ('oeste', (i, j-1), 0.05)]),
            'este':  ((i, j+1), 0.90, [('norte', (i-1, j), 0.05), ('sur', (i+1, j), 0.05)]),
            'oeste': ((i, j-1), 0.90, [('norte', (i-1, j), 0.05), ('sur', (i+1, j), 0.05)])
        }
        
        primaria, prob_primaria, secundarias = desplazamientos_direccion[direccion_principal]

        # Dirección primaria
        if 0 <= primaria[0] < len(mapa) and 0 <= primaria[1] < len(mapa[0]) and mapa[primaria[0]][primaria[1]] not in "_M":
            P[indice_actual][indice_actual] -= prob_primaria
            P[indice_actual][indice_estado(primaria)] = prob_primaria

        # Direcciones secundarias
        for direccion, pos, prob in secundarias:
            if 0 <= pos[0] < len(mapa) and 0 <= pos[1] < len(mapa[0]) and mapa[pos[0]][pos[1]] not in "_M":
                P[indice_actual][indice_actual] -= prob
                P[indice_actual][indice_estado(pos)] = prob

    return P

def imprimir_matriz(matriz):
    for fila in matriz:
        print(["{:.2f}".format(max(0, prob)) if abs(prob) < 1e-10 else "{:.2f}".format(prob) for prob in fila])

# Funciones del robot
def dibujar_mapa(mapa, pantalla):
    for fila in range(len(mapa)):
        for columna in range(len(mapa[0])):
            color = NEGRO if mapa[fila][columna] == 'M' else GRIS if mapa[fila][columna] == '_' else BLANCO
            pygame.draw.rect(pantalla, color, (columna*TAM_BLOQUE, fila*TAM_BLOQUE, TAM_BLOQUE, TAM_BLOQUE))
            pygame.draw.line(pantalla, NEGRO, (columna*TAM_BLOQUE, 0), (columna*TAM_BLOQUE, ALTO))
        pygame.draw.line(pantalla, NEGRO, (0, fila*TAM_BLOQUE), (ANCHO, fila*TAM_BLOQUE))

    # Dibujar el robot y la meta
    pygame.draw.rect(pantalla, AZUL, (posicion_robot[1]*TAM_BLOQUE, posicion_robot[0]*TAM_BLOQUE, TAM_BLOQUE, TAM_BLOQUE))
    pygame.draw.rect(pantalla, AZUL if ejemplo_mapa[5][3] == 'R' else ROJO, (3*TAM_BLOQUE, 5*TAM_BLOQUE, TAM_BLOQUE, TAM_BLOQUE))
    if not instrucciones:
        font = pygame.font.SysFont(None, 30)
        texto = font.render("Recorrido terminado", True, NEGRO)
        pantalla.blit(texto, texto.get_rect(center=(ANCHO // 2, ALTO // 4)))



meta_alcanzada = False  # Esto marca si la meta ha sido alcanzada
pasos_totales = 0  # Contador total de pasos realizados por el robot
errores = 0  # Contador de errores (movimientos no intencionales)

NUMERO_MAXIMO_PASOS = 1000

def mover_robot():
    global posicion_robot, ejemplo_mapa, pantalla, meta_alcanzada, pasos_totales, errores

    # Si la meta ha sido alcanzada o se han excedido los pasos máximos, no se mueve el robot
    if meta_alcanzada or pasos_totales >= NUMERO_MAXIMO_PASOS:
        return

    i, j = posicion_robot
    desplazamientos_direccion = {
        'norte': ((i-1, j), 0.20, [('este', (i, j+1), 0.40), ('oeste', (i, j-1), 0.40)]),
        'sur':   ((i+1, j), 0.20, [('este', (i, j+1), 0.40), ('oeste', (i, j-1), 0.40)]),
        'este':  ((i, j+1), 0.20, [('norte', (i-1, j), 0.40), ('sur', (i+1, j), 0.40)]),
        'oeste': ((i, j-1), 0.20, [('norte', (i-1, j), 0.40), ('sur', (i+1, j), 0.40)])
    }

    # Obtener la dirección desde la política
    direccion_principal = ['norte', 'sur', 'este', 'oeste'][instrucciones[estados.index((i, j))]]
    movimiento_principal, prob_principal, movimientos_secundarios = desplazamientos_direccion[direccion_principal]

    # Crear la lista de movimientos basada en probabilidades
    movimientos = [movimiento_principal] * int(prob_principal * 100) + \
                   [movimientos_secundarios[0][1]] * int(movimientos_secundarios[0][2] * 100) + \
                   [movimientos_secundarios[1][1]] * int(movimientos_secundarios[1][2] * 100)

    # Limitar el número de pasos a un máximo de NUMERO_MAXIMO_PASOS
    movimientos = movimientos[:NUMERO_MAXIMO_PASOS]

    # Elegir un movimiento basado en la probabilidad
    nueva_posicion = random.choice(movimientos)
    pasos_totales += 1

    # Verificar si se realizó un movimiento erróneo
    if nueva_posicion != movimiento_principal:
        errores += 1

    # Verificar si la nueva posición es válida
    if (0 <= nueva_posicion[0] < len(ejemplo_mapa) and
        0 <= nueva_posicion[1] < len(ejemplo_mapa[0]) and
        ejemplo_mapa[nueva_posicion[0]][nueva_posicion[1]] not in "_M"):
        posicion_robot = nueva_posicion

        # Verificar si el robot llegó a la meta
        if posicion_robot == (5, 3):  # Asegúrate de ajustar estas coordenadas a las de tu meta
            ejemplo_mapa[5][3] = 'R'  # Marcar la meta como alcanzada
            meta_alcanzada = True  # Detener movimientos futuros
            print("¡Meta alcanzada!")

        # Redibujar el mapa con la nueva posición del robot
        pantalla.fill(BLANCO)
        dibujar_mapa(ejemplo_mapa, pantalla)
        pygame.display.flip()
        pygame.time.wait(500)

    # Imprimir estadísticas de movimiento
    print(f"Total de pasos: {pasos_totales}, Errores: {errores}")


def seleccionar_posicion_inicial_aleatoria(mapa):
    posiciones_validas = [
        (i, j) for i in range(len(mapa)) for j in range(len(mapa[0]))
        if mapa[i][j] not in ('M', '_')
    ]
    return random.choice(posiciones_validas)
######################################################################################################################
pygame.init()

# Definir el tamaño de los bloques y del mapa
ejemplo_mapa = [
    [ ' '  ,  ' ' ,  ' '  ,  ' '  ,  ' '  ,  ' '  ,  ' '  , '_'  ,  '_'  ],
    [ ' '  ,  '_' ,  '_'  ,  ' '  ,  '_'  ,  '_'  ,  ' '  , '_'  ,  '_'  ],
    [ ' '  ,  ' ' ,  '_'  ,  ' '  ,  '_'  ,  '_'  ,  ' '  , '_'  ,  '_'  ],
    [ 'M'  ,  ' ' ,  ' '  ,  'M'  ,  ' '  ,  ' '  ,  ' '  , ' '  ,  ' '  ],
    [ ' '  ,  ' ' ,  '_'  ,  ' '  ,  ' '  ,  '_'  ,  ' '  , '_'  ,  '_'  ],
    [ ' '  ,  '_' ,  '_'  ,  ' '  ,  '_'  ,  '_'  ,  ' '  , '_'  ,  '_'  ],
    [ ' '  ,  ' ' ,  ' '  ,  ' '  ,  '_'  ,  '_'  ,  '_'  , '_'  ,  '_'  ]
]
TAM_BLOQUE = 40
ANCHO = len(ejemplo_mapa[0]) * TAM_BLOQUE
ALTO = len(ejemplo_mapa) * TAM_BLOQUE

# Cargar modelo de Markov
estados = mapear_a_estados(ejemplo_mapa)
P1 = construir_matriz_transicion(ejemplo_mapa, estados, 'norte')
P2 = construir_matriz_transicion(ejemplo_mapa, estados, 'sur')
P3 = construir_matriz_transicion(ejemplo_mapa, estados, 'este')
P4 = construir_matriz_transicion(ejemplo_mapa, estados, 'oeste')

Ld = 0.90
nMETA = 27

def nRw(nS, nA):
    if nS == nMETA:
        return +100
    else:
        return 0.1

nS = len(P1)
nA = 4
nE = 0.0001
aQ = [[0]*nA for i in range(nS)]
aP = []
a0 = [+0 for i in range(0, 33)]
a1 = [+1 for i in range(0, 33)]
a2 = [-1 for i in range(0, 33)]
aT = []
aE = []
nK = 1

aT = [P1, P2, P3, P4]
aE.append(a1)
aP.append(a0)

while nK < 1000:
    aE.append(a0)
    aP.append(a2)
    for s in range(0, nS):
        for a in range(0, nA):
            aAux = [aT[a][s][i] * aE[nK - 1][i] for i in range(0, nS)]
            aQ[s][a] = nRw(s, a) + Ld * sum(aAux)
        aX = aQ[s][:]
        aE[nK][s] = max(aX)
        aP[nK][s] = aX.index(max(aX))   
    nK += 1

print("Esta es la política final óptima:")
print(aP[-1])

instrucciones = aP[-1]  # Asignar las instrucciones obtenidas del modelo de Markov
# time.sleep(2)
# Configurar la pantalla
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Mapa")

# Posición inicial del robot
posicion_robot = (0,0)

# Bucle principal del juego
reloj = pygame.time.Clock()
jugando = True
while jugando:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            jugando = False  # Salir del bucle si se cierra la ventana
        elif evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                jugando = False  # Salir del bucle si se presiona la tecla Escape

    # Mover el robot según la política óptima para su estado actual
    mover_robot()

# Salir de Pygame
pygame.quit()
sys.exit()
