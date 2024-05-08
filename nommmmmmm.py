import pygame
import sys
import time
import random
import matplotlib.pyplot as plt
import numpy as np
# Definir coloress
BLANCO, NEGRO, GRIS, ROJO, AZUL, VERDE = (255, 255, 255), (0, 0, 0), (128, 128, 128), (255, 0, 0), (0, 0, 255), (0, 255, 0)
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
# Indicador para controlar la visualización gráfica
mostrar_graficos = True
nRw_values = []


def mover_robot(visualizar=True):
    global posicion_robot, ejemplo_mapa, pantalla, meta_alcanzada, pasos_totales, errores, nRw_values,prob_principal, prob_secundaria

    if pasos_totales >= NUMERO_MAXIMO_PASOS or meta_alcanzada:      
        return

    i, j = posicion_robot
    desplazamientos_direccion = {
        'norte': ((i-1, j), prob_principal, [('este', (i, j+1), prob_secundaria), ('oeste', (i, j-1), prob_secundaria)]),
        'sur':   ((i+1, j), prob_principal, [('este', (i, j+1), prob_secundaria), ('oeste', (i, j-1), prob_secundaria)]),
        'este':  ((i, j+1), prob_principal, [('norte', (i-1, j), prob_secundaria), ('sur', (i+1, j), prob_secundaria)]),
        'oeste': ((i, j-1), prob_principal, [('norte', (i-1, j), prob_secundaria), ('sur', (i+1, j), prob_secundaria)])
    }

    direccion_principal = ['norte', 'sur', 'este', 'oeste'][instrucciones[estados.index((i, j))]]
    movimiento_principal, prob_principal, movimientos_secundarios = desplazamientos_direccion[direccion_principal]

    movimientos = [movimiento_principal] * int(prob_principal * 100) + \
                   [movimientos_secundarios[0][1]] * int(movimientos_secundarios[0][2] * 100) + \
                   [movimientos_secundarios[1][1]] * int(movimientos_secundarios[1][2] * 100)

    nueva_posicion = random.choice(movimientos)
    pasos_totales += 1

    if nueva_posicion != movimiento_principal:
        errores += 1
    # Penalización por movimiento no óptimo
    penalizacion = -10 if nueva_posicion != movimiento_principal else 10
    nRw_values.append(penalizacion)  # Acumula valores de nRw con subidas y bajadas

    if (0 <= nueva_posicion[0] < len(ejemplo_mapa) and
        0 <= nueva_posicion[1] < len(ejemplo_mapa[0]) and
        ejemplo_mapa[nueva_posicion[0]][nueva_posicion[1]] not in "_M"):
        posicion_robot = nueva_posicion
        recompensa_actual = nRw(estados.index(posicion_robot), 0)
        nRw_values[-1] += recompensa_actual  # Ajusta el último valor acumulado con la recompensa actual

        if posicion_robot == (5, 3):  # Coordenadas de la meta
            ejemplo_mapa[5][3] = 'R'
            meta_alcanzada = True
            graficar_nRw_acumulado()

        
        if visualizar:           
            pantalla.fill(BLANCO)
            dibujar_mapa(ejemplo_mapa, pantalla)
            pygame.display.flip()
            pygame.time.wait(500)
            

def graficar_nRw_acumulado():
    """Función para graficar el nRw acumulado."""
    plt.figure(figsize=(10, 5))
    plt.plot(range(len(nRw_values)), nRw_values, label='nRw por paso')
    plt.plot(range(len(nRw_values)), np.cumsum(nRw_values), label='nRw acumulado', color='red')
    plt.xlabel('Pasos')
    plt.ylabel('Valor de nRw')
    plt.title('Valor Acumulado de nRw')
    plt.legend()
    plt.grid(True)
    plt.show()

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

def resetear_estado():
    global posicion_robot, instrucciones, ejemplo_mapa, meta_alcanzada, pasos_totales, errores
    # Restablecer el mapa a su estado inicial
    ejemplo_mapa = [
        [' ', ' ', ' ', ' ', ' ', ' ', ' ', '_', '_'],
        [' ', '_', '_', ' ', '_', '_', ' ', '_', '_'],
        [' ', ' ', '_', ' ', '_', '_', ' ', '_', '_'],
        ['M', ' ', ' ', 'M', ' ', ' ', ' ', ' ', ' '],
        [' ', ' ', '_', ' ', ' ', '_', ' ', '_', '_'],
        [' ', '_', '_', ' ', '_', '_', ' ', '_', '_'],
        [' ', ' ', ' ', ' ', '_', '_', '_', '_', '_']
    ]
    # Seleccionar una posición inicial aleatoria para el robot que no esté bloqueada
    posicion_robot = seleccionar_posicion_inicial_aleatoria(ejemplo_mapa)
    # Reiniciar las instrucciones
    instrucciones = []
    # Restablecer las variables de estado
    meta_alcanzada = False
    pasos_totales = 0
    errores = 0


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

instrucciones = aP[-1]  # Asignar las instrucciones obtenidas del modelo de Markov

mostrar_menu = True
###################################################
#ALGORITMOS
# Función para ejecutar un algoritmo basado en la selección
def ejecutar_algoritmo(seleccion):
    global instrucciones
    global aP
    iteraciones_resultados = []  # Lista para almacenar los resultados de cada iteración completa

    if seleccion == "Value Iteration Clásico":
        Ld = 0.9
        nK = 1
        aE = [a1]  # Suponiendo que a1 está definido previamente
        aP = [a0]  # Suponiendo que a0 está definido previamente
        aQ = [[0] * nA for _ in range(nS)]  # nS y nA deben estar definidos
        # Suponiendo que aT está definido previamente y contiene matrices de transición
        while nK < 1000:
            aE.append(a0.copy())  # Se añade una copia para evitar referencias duplicadas
            aP.append(a2.copy())  # Se añade una copia por la misma razón
            for s in range(nS):
                for a in range(nA):
                    aAux = [aT[a][s][i] * aE[nK - 1][i] for i in range(nS)]
                    aQ[s][a] = nRw(s, a) + Ld * sum(aAux)
                aX = aQ[s][:]
                aE[nK][s] = max(aX)
                aP[nK][s] = aX.index(max(aX))
            nK += 1
            
        instrucciones = aP[-1]  # Asignar las instrucciones obtenidas del modelo de Markov
        # print("Instrucciones finales:", instrucciones)
        return instrucciones
    
    elif seleccion == "Relative Value Iteration":
        Ld = 0.9
        V = [0] * nS  # Vector de valores inicializado a 0
        policy = [0] * nS  # Política inicial arbitraria
        delta = float('inf')
        epsilon = 0.0001
        iteracion = 0  # Contador de iteraciones

        while delta > epsilon and iteracion < 1000:  # Añadir límite de iteraciones
            delta = 0
            for s in range(nS):
                v = V[s]
                # Calcular el valor máximo para este estado considerando las probabilidades más recientes
                V[s] = max([sum([aT[a][s][sp] * (nRw(sp, a) + Ld * V[sp]) for sp in range(nS)]) for a in range(nA)])
                # Actualizar delta para verificar la condición de convergencia
                delta = max(delta, abs(v - V[s]))
            
            # Normalización de valores para estabilidad numérica
            v_min = min(V)
            V = [v - v_min for v in V]  # Reducir todos los valores por el mínimo valor encontrado
            
            # Actualización de la política basada en los valores calculados
            for s in range(nS):
                policy[s] = max(range(nA), key=lambda a: sum([aT[a][s][sp] * (nRw(sp, a) + Ld * V[sp]) for sp in range(nS)]))

            iteracion += 1  # Incrementar el contador de iteraciones

        print("Política óptima calculada usando Relative Value Iteration:", policy)
        aP.append(policy)
        print("Política óptima calculada usando Relative Value Iteration:", policy)
        instrucciones = aP[-1]  # Asignar las instrucciones obtenidas del modelo de Markov
        print("Instrucciones finales:", instrucciones)
        return instrucciones
            
    elif seleccion == "Gauss-Seidel Value Iteration":
        Ld = 0.9
        V = [0] * nS  # Vector de valores inicializado a 0
        policy = [0] * nS  # Política inicial arbitraria
        delta = float('inf')
        epsilon = 0.0001
        iteracion = 0  # Contador de iteraciones

        while delta > epsilon and iteracion < 1000:  # Añadir límite de iteraciones
            delta = 0
            for s in range(nS):
                v = V[s]
                # Calcular el nuevo valor para el estado s usando los valores más recientes de V
                V[s] = max([sum([aT[a][s][sp] * (nRw(sp, a) + Ld * V[sp]) for sp in range(nS)]) for a in range(nA)])
                # Actualizar delta para verificar la condición de convergencia
                delta = max(delta, abs(v - V[s]))

            # Actualización de la política basada en los valores calculados en el paso actual
            for s in range(nS):
                policy[s] = max(range(nA), key=lambda a: sum([aT[a][s][sp] * (nRw(sp, a) + Ld * V[sp]) for sp in range(nS)]))

            iteracion += 1  # Incrementar el contador de iteraciones

        print("Política óptima calculada usando Gauss-Seidel Value Iteration:", policy)
        aP.append(policy)
        print("Política óptima calculada usando Gauss-Seidel Value Iteration:", policy)
        instrucciones = aP[-1]  # Asignar las instrucciones obtenidas del modelo de Markov
        print("Instrucciones finales:", instrucciones)
        return instrucciones
    elif seleccion == "Value Iteration con Descuento 0.98":
        Ld = 0.98  # Establece el factor de descuento a 0.98
        V = [0] * nS  # Vector de valores inicializado a 0
        policy = [0] * nS  # Política inicial arbitraria
        delta = float('inf')
        epsilon = 0.0001
        iteracion = 0  # Contador de iteraciones

        while delta > epsilon and iteracion < 1000:  # Añadir límite de iteraciones
            delta = 0
            for s in range(nS):
                v = V[s]
                # Calcular el nuevo valor para el estado s
                V[s] = max([sum([aT[a][s][sp] * (nRw(sp, a) + Ld * V[sp]) for sp in range(nS)]) for a in range(nA)])
                # Actualizar delta para verificar la condición de convergencia
                delta = max(delta, abs(v - V[s]))

            # Actualización de la política basada en los valores calculados
            for s in range(nS):
                policy[s] = max(range(nA), key=lambda a: sum([aT[a][s][sp] * (nRw(sp, a) + Ld * V[sp]) for sp in range(nS)]))

            iteracion += 1  # Incrementar el contador de iteraciones

        print("Política óptima calculada usando Value Iteration con Descuento 0.98:", policy)
        aP.append(policy)
        print("Política óptima calculada usando Value Iteration con Descuento 0.98:", policy)
        instrucciones = aP[-1]  # Asignar las instrucciones obtenidas del modelo de Markov
        print("Instrucciones finales:", instrucciones)
        return instrucciones
    
    elif seleccion == "Relative Value Iteration con Descuento 0.98":
        Ld = 0.98  # Factor de descuento ajustado a 0.98
        V = [0] * nS  # Vector de valores inicializado a 0
        policy = [0] * nS  # Política inicial arbitraria
        delta = float('inf')
        epsilon = 0.0001
        iteracion = 0  # Contador de iteraciones

        while delta > epsilon and iteracion < 1000:  # Añadir límite de iteraciones
            delta = 0
            for s in range(nS):
                v = V[s]
                # Calcular el valor máximo para este estado
                V[s] = max([sum([aT[a][s][sp] * (nRw(sp, a) + Ld * V[sp]) for sp in range(nS)]) for a in range(nA)])
                delta = max(delta, abs(v - V[s]))
            
            # Normalización de valores para estabilidad numérica
            v_min = min(V)
            V = [v - v_min for v in V]  # Reducir todos los valores por el mínimo valor encontrado
            
            # Actualización de la política basada en los valores calculados
            for s in range(nS):
                policy[s] = max(range(nA), key=lambda a: sum([aT[a][s][sp] * (nRw(sp, a) + Ld * V[sp]) for sp in range(nS)]))

            iteracion += 1  # Incrementar el contador de iteraciones

        print("Relative Value Iteration con Descuento 0.98:", policy)
        aP.append(policy)
        print("Política óptima calculada usando Relative Value Iteration con Descuento 0.98:", policy)
        instrucciones = aP[-1]  # Asignar las instrucciones obtenidas del modelo de Markov
        print("Instrucciones finales:", instrucciones)
        return instrucciones

    elif seleccion == "Q-Value Iteration Clásico":
        Ld = 0.9  # Factor de descuento
        Q = [[0 for _ in range(nA)] for _ in range(nS)]  # Inicializa la tabla Q
        epsilon = 0.0001
        iteracion = 0  # Contador de iteraciones
        delta = float('inf')

        while delta > epsilon and iteracion < 1000:  # Añadir límite de iteraciones
            delta = 0
            for s in range(nS):
                for a in range(nA):
                    q_old = Q[s][a]
                    # Calcular el nuevo valor Q para cada acción a en el estado s
                    Q[s][a] = sum([aT[a][s][sp] * (nRw(sp, a) + Ld * max(Q[sp])) for sp in range(nS)])
                    delta = max(delta, abs(q_old - Q[s][a]))  # Actualizar delta

            iteracion += 1  # Incrementar el contador de iteraciones

        # Extraer la política óptima de la tabla Q
        policy = [max(range(nA), key=lambda a: Q[s][a]) for s in range(nS)]
        aP.append(policy)
        print("Política óptima calculada usando Q-Value Iteration Clásico:", policy)
        instrucciones = aP[-1]  # Asignar las instrucciones obtenidas del modelo de Markov
        print("Instrucciones finales:", instrucciones)
        return instrucciones

# Antes del bucle principal del juego, inicializa las instrucciones globalmente

    elif seleccion == "Q-Value Iteration con Descuento 0.98":
        Ld = 0.98  # Establece el factor de descuento a 0.98
        Q = [[0 for _ in range(nA)] for _ in range(nS)]  # Inicializa la tabla Q para cada estado y acción
        epsilon = 0.0001
        iteracion = 0  # Contador de iteraciones
        delta = float('inf')

        while delta > epsilon and iteracion < 1000:  # Añadir límite de iteraciones
            delta = 0
            for s in range(nS):
                for a in range(nA):
                    q_old = Q[s][a]
                    # Calcular el nuevo valor Q para cada acción a en el estado s
                    Q[s][a] = sum([aT[a][s][sp] * (nRw(sp, a) + Ld * max(Q[sp])) for sp in range(nS)])
                    delta = max(delta, abs(q_old - Q[s][a]))  # Actualizar delta
            iteracion += 1  # Incrementar el contador de iteraciones

        # Extraer la política óptima de la tabla Q
        policy = [max(range(nA), key=lambda a: Q[s][a]) for s in range(nS)]
        aP.append(policy)
        print("Política óptima calculada usando Q-Value Iteration con Descuento 0.98:", policy)
        instrucciones = aP[-1]  # Asignar las instrucciones obtenidas del modelo de Markov
        print("Instrucciones finales:", instrucciones)
        return instrucciones

def ejecutar_simulaciones_algoritmo(algoritmo, num_simulaciones= 20):
    resultados_pasos = []
    # Primera iteración con visualización
    resetear_estado()
    ejecutar_algoritmo(algoritmo)
    while not meta_alcanzada and pasos_totales < NUMERO_MAXIMO_PASOS:
        mover_robot(visualizar=True)

    resultados_pasos.append(pasos_totales)

    # Iteraciones adicionales sin visualización
    for _ in range(1, num_simulaciones):
        resetear_estado()
        ejecutar_algoritmo(algoritmo)
        while not meta_alcanzada and pasos_totales < NUMERO_MAXIMO_PASOS:
            mover_robot(visualizar=False)
        resultados_pasos.append(pasos_totales)

    # Graficar los resultados de la simulación
    plt.figure(figsize=(8, 4))
    plt.bar(range(1, num_simulaciones + 1), resultados_pasos, color='blue')
    plt.xlabel('Iteración')
    plt.ylabel('Pasos necesarios para alcanzar la meta')
    plt.title('Resultados de las Simulaciones')
    plt.xticks(range(1, num_simulaciones + 1))
    plt.grid(True)
    plt.show()

    return resultados_pasos


def mostrar_resultados(resultados):
    pantalla.fill(BLANCO)  # Limpia la pantalla
    y_pos = 50
    for i, resultado in enumerate(resultados):
        text = font.render(f"Simulación {i + 1}: {resultado} pasos", True, NEGRO)
        pantalla.blit(text, (50, y_pos))
        y_pos += 40  # Incrementa la posición y para el próximo texto
    pygame.display.flip()  # Actualiza la pantalla

# Llamar a mostrar_resultados en el bucle principal si se ha completado una simulación
    if not mostrar_menu and mostrar_home:
     mostrar_resultados(resultados)  
# Solicitar probabilidades al usuario
prob_principal = float(input("Introduce la probabilidad para la dirección principal (e.g., 0.90): "))
prob_secundaria = (1 - prob_principal) / 2
# Configurar la pantalla
pantalla = pygame.display.set_mode((550, 600))
pygame.display.set_caption('Seleccionar Algoritmo')

# Fuente para el texto
font = pygame.font.Font(None, 30)
# Lista de algoritmos
algorithms = [
    "Value Iteration Clásico",
    "Relative Value Iteration",
    "Gauss-Seidel Value Iteration",
    "Value Iteration con Descuento 0.98",
    "Relative Value Iteration con Descuento 0.98",
    "Q-Value Iteration Clásico",
    "Q-Value Iteration con Descuento 0.98"
]

# Crear botones para cada algoritmo
buttons = []
for i, alg in enumerate(algorithms):
    buttons.append(pygame.Rect(50, 30 + i*70, 300, 50))

# Función para dibujar el menú
def draw_menu():
    pantalla.fill(BLANCO)
    for i, button in enumerate(buttons):
        pygame.draw.rect(pantalla, VERDE, button)  # Dibuja el botón
        text = font.render(algorithms[i], True, NEGRO)  # Renderiza el texto del botón
        text_rect = text.get_rect()  # Obtiene el rectángulo del texto
        text_rect.center = button.center  # Centra el texto en el botón
        pantalla.blit(text, text_rect)  # Dibuja el texto en la pantalla
    pygame.display.flip()  # Actualiza la pantalla completa

# Función para dibujar el botón Home
def draw_home_button():
    pygame.draw.rect(pantalla, VERDE, home_button)  # Dibuja el botón
    text = font.render("Home", True, NEGRO)
    text_rect = text.get_rect()
    text_rect.center = home_button.center
    pantalla.blit(text, text_rect)

def draw_simulation_button():
    pygame.draw.rect(pantalla, VERDE, simulation_button)  # Dibuja el botón
    text = font.render("Simulación", True, NEGRO)
    text_rect = text.get_rect()
    text_rect.center = simulation_button.center
    pantalla.blit(text, text_rect)

    
# Asegúrate de que el tamaño del botón es suficiente para el texto
button_width = max(font.size(alg)[0] for alg in algorithms) + 20  # Agrega un poco de margen
buttons = [pygame.Rect(50, 30 + i*70, button_width, 50) for i, alg in enumerate(algorithms)]


# Definición del botón Home
home_button = pygame.Rect(50, 520, 150, 50)

# Definición del botón Simulación
simulation_button = pygame.Rect(210, 520, 150, 50)  # Asegúrate de que los botones no se superpongan


# Posición inicial del robot
posicion_robot = (0,0)

# Bucle principal del juego
reloj = pygame.time.Clock()
# Al inicio de tu código, define la variable global
algoritmo_seleccionado = None

# Modificar el bucle principal para incluir el reseteo del estado
jugando = True
while jugando:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            jugando = False
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = evento.pos
            if mostrar_menu:
                for i, button in enumerate(buttons):
                    if button.collidepoint(mouse_pos):
                        print(f"Ejecutando {algorithms[i]}")
                        resetear_estado()
                        instrucciones = ejecutar_algoritmo(algorithms[i])
                        algoritmo_seleccionado = algorithms[i]  # Guarda el algoritmo seleccionado
                        mostrar_menu = False
                        mostrar_home = True

            elif mostrar_home:
                if home_button.collidepoint(mouse_pos):
                    mostrar_menu = True
                    mostrar_home = False
                elif simulation_button.collidepoint(mouse_pos) and algoritmo_seleccionado is not None:
                    # Ejecuta las simulaciones para el algoritmo seleccionado
                    print(f"Ejecutando simulaciones para {algoritmo_seleccionado}")
                    resultados = ejecutar_simulaciones_algoritmo(algoritmo_seleccionado, 10)
                    print(f"Resultados de simulación para {algoritmo_seleccionado}: {resultados}")
                    mostrar_menu = True  # Decide si quieres volver al menú o hacer algo más


    pantalla.fill(BLANCO)
    if mostrar_menu:
        draw_menu()
    else:
        if mostrar_home:
            draw_home_button()
            draw_simulation_button()
        dibujar_mapa(ejemplo_mapa, pantalla)
        if instrucciones and not mostrar_menu:
            mover_robot()
            pygame.display.flip()
            time.sleep(0.001)

pygame.quit()
sys.exit()
