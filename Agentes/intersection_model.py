from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
import random

class CocheNormal(Agent):
    def __init__(self, unique_id, model, destino, estado="tranquilo"):
        super().__init__(unique_id, model)
        self.destino = destino  # a donde va el coche
        self.estado = estado  # si está "tranquilo" o "enojado"
        self.tiempo_llegada = None
        self.velocidad = 1
        self.en_punto_cambio = False  # indica si ya está en el punto donde cambia de dirección
        self.carril_original = None  # guarda el carril inicial del coche
        self.punto_cambio = None  # punto de cambio antes del semáforo

    def step(self):
        # si no ha llegado al punto de cambio, se mueve hacia allá
        if not self.en_punto_cambio:
            self.mover_hacia_punto_cambio()
        else:
            self.cambiar_direccion_y_continuar()  # si ya llegó al punto de cambio, sigue hacia su destino final

        self.verificar_destino()  # verifica si llegó a su destino final y si sí, se elimina del modelo

    def establecer_punto_cambio(self):
        # define el punto de cambio justo antes del semáforo, depende de por dónde venga
        centro_x = self.model.grid.width // 2
        centro_y = self.model.grid.height // 2

        if self.pos[1] == 0:  # desde el sur
            self.punto_cambio = (self.carril_original, centro_y - 1)
        elif self.pos[1] == self.model.grid.height - 1:  # desde el norte
            self.punto_cambio = (self.carril_original, centro_y + 1)
        elif self.pos[0] == 0:  # desde el oeste
            self.punto_cambio = (centro_x - 1, self.carril_original)
        elif self.pos[0] == self.model.grid.width - 1:  # desde el este
            self.punto_cambio = (centro_x + 1, self.carril_original)

    def mover_hacia_punto_cambio(self):
        # define el carril original si aún no lo ha hecho
        if self.carril_original is None:
            self.carril_original = self.pos[0] if self.pos[1] in [0, self.model.grid.height - 1] else self.pos[1]

        if self.punto_cambio is None:
            self.establecer_punto_cambio()  # si aún no tiene un punto de cambio definido, lo establece

        if self.punto_cambio is None:
            print(f"Error: punto de cambio no definido para el coche {self.unique_id}")
            return

        # verificar si el punto de cambio está ocupado
        ocupantes = [agent for agent in self.model.grid.get_cell_list_contents(self.punto_cambio) if isinstance(agent, CocheNormal)]
        if ocupantes:
            if self.estado == "tranquilo":
                # si el coche es "tranquilo", busca un carril alternativo
                adjacent_positions = [
                    (self.punto_cambio[0] - 1, self.punto_cambio[1]),
                    (self.punto_cambio[0] + 1, self.punto_cambio[1]),
                    (self.punto_cambio[0], self.punto_cambio[1] - 1),
                    (self.punto_cambio[0], self.punto_cambio[1] + 1)
                ]
                for pos in adjacent_positions:
                    if self.model.grid.out_of_bounds(pos):
                        continue
                    # busca un carril "calle" libre sin coches
                    if any(isinstance(agent, Calle) and agent.tipo == "calle" for agent in self.model.grid.get_cell_list_contents(pos)):
                        if not any(isinstance(agent, CocheNormal) for agent in self.model.grid.get_cell_list_contents(pos)):
                            self.punto_cambio = pos  # cambia el punto de cambio al carril alternativo
                            break
            else:
                # si el coche es "enojado", imprime colisión y no cambia de carril
                print(f"Colisión en el punto de cambio: Coche {self.unique_id} (enojado) colisionó con otro coche en {self.punto_cambio}")
                return

        # mover el coche hacia el punto de cambio
        nueva_pos = self.pos
        if self.pos[0] < self.punto_cambio[0]:
            nueva_pos = (self.pos[0] + self.velocidad, self.pos[1])
        elif self.pos[0] > self.punto_cambio[0]:
            nueva_pos = (self.pos[0] - self.velocidad, self.pos[1])

        if self.pos[1] < self.punto_cambio[1]:
            nueva_pos = (self.pos[0], self.pos[1] + self.velocidad)
        elif self.pos[1] > self.punto_cambio[1]:
            nueva_pos = (self.pos[0], self.pos[1] - self.velocidad)

        self.model.grid.move_agent(self, nueva_pos)  # mueve el coche

        # si llegó al punto de cambio, actualiza el estado y notifica al semáforo
        if self.pos == self.punto_cambio:
            self.en_punto_cambio = True
            self.calcular_tiempo_llegada()
            self.model.semaforo.recibir_mensaje(self)

    def cambiar_direccion_y_continuar(self):
        # cambia de dirección hacia su destino final
        if self.destino == "arriba" and self.pos[1] > 0:
            self.model.grid.move_agent(self, (self.pos[0], self.pos[1] - self.velocidad))
        elif self.destino == "derecha" and self.pos[0] < self.model.grid.width - 1:
            self.model.grid.move_agent(self, (self.pos[0] + self.velocidad, self.pos[1]))
        elif self.destino == "izquierda" and self.pos[0] > 0:
            self.model.grid.move_agent(self, (self.pos[0] - self.velocidad, self.pos[1]))

    def calcular_tiempo_llegada(self):
        # calcula el tiempo en que va a llegar al semáforo
        distancia = abs(self.pos[1] - (self.model.grid.height // 2)) if self.destino == "arriba" else \
                    abs(self.pos[0] - (self.model.grid.width // 2))
        self.tiempo_llegada = distancia // self.velocidad
        print(f"Coche {self.unique_id}: Llegaré al semáforo en {self.tiempo_llegada} turnos.")

    def verificar_destino(self):
        # verifica si ya llegó al destino final y lo elimina si es así
        if (self.destino == "arriba" and self.pos[1] == 0) or \
           (self.destino == "derecha" and self.pos[0] == self.model.grid.width - 1) or \
           (self.destino == "izquierda" and self.pos[0] == 0):
            print(f"Coche {self.unique_id} ha llegado a su destino final en {self.destino}.")
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)



#Agente adicionales
class CocheRapido(CocheNormal):
    def __init__(self, unique_id, model, destino, estado="tranquilo"):
        super().__init__(unique_id, model, destino, estado)
        self.velocidad = 2  # Velocidad más rápida

    def step(self):
        # Usa la lógica completa de CocheNormal, pero más rápido
        super().step()


class CocheLento(CocheNormal):
    def __init__(self, unique_id, model, destino, estado="tranquilo"):
        super().__init__(unique_id, model, destino, estado)
        self.velocidad = 1  # Velocidad más lenta

    def step(self):
        # Usa la lógica completa de CocheNormal, pero más lento
        super().step()


class CocheDesobediente(CocheNormal):
    def __init__(self, unique_id, model, destino, estado="tranquilo"):
        super().__init__(unique_id, model, destino, estado)
        self.desobediente = True  # Este coche ignora señales

    def step(self):
        # Decide si ignora el semáforo
        if self.en_punto_cambio and random.random() < 0.5:  # 50% de las veces ignora el semáforo
            print(f"Coche {self.unique_id} (desobediente) ignora el semáforo en {self.punto_cambio}.")
            self.en_punto_cambio = False  # Ignora la lógica del semáforo
            self.cambiar_direccion_y_continuar()  # Sigue su camino sin esperar

        # Si no ignora, usa la lógica completa de CocheNormal
        else:
            super().step()

class CocheObstructor(CocheNormal):
    def __init__(self, unique_id, model, destino, estado="tranquilo"):
        super().__init__(unique_id, model, destino, estado)
        self.obstruyendo = True  # Indica que bloquea el paso

    def step(self):
        # Se queda en su lugar e imprime su estado
        print(f"Coche {self.unique_id} (obstructor) está bloqueando el paso en {self.pos}.")
        # No llama a `super().step()` para evitar movimiento


class Semaforo(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.estado = "amarillo"  # estado inicial del semáforo
        self.color = "yellow"
        self.vehiculos_en_espera = []
        self.ciclo = ["norte", "sur", "este", "oeste"]
        self.ciclo_index = 0
        self.saturado = False

    def recibir_mensaje(self, coche):
        # recibe mensaje del coche que indica cuánto falta para llegar al semáforo
        print(f"Semáforo: Recibido mensaje de Coche {coche.unique_id} que llegará en {coche.tiempo_llegada} turnos.")
        self.vehiculos_en_espera.append((coche, coche.tiempo_llegada))
        if len(self.vehiculos_en_espera) > 5:
            self.saturado = True

    def step(self):
        if self.saturado:
            # modo cíclico cuando está saturado, cambia el semáforo para distintas direcciones
            direccion_actual = self.ciclo[self.ciclo_index]
            print(f"Semáforo en modo cíclico para la dirección: {direccion_actual}")
            self.estado = "verde" if self.estado == "rojo" else "rojo"
            self.color = "green" if self.estado == "verde" else "red"
            self.ciclo_index = (self.ciclo_index + 1) % len(self.ciclo)
            print(f"Semáforo cambia a {self.estado} en modo cíclico.")
        else:
            # da paso al coche que tiene menor tiempo de llegada si no está saturado
            if self.vehiculos_en_espera:
                coche, _ = min(self.vehiculos_en_espera, key=lambda x: x[1])
                print(f"Semáforo: Dando paso a Coche {coche.unique_id}.")
                self.estado = "verde"
                self.color = "green"
                self.vehiculos_en_espera.remove((coche, coche.tiempo_llegada))
            else:
                # cambia a amarillo si no hay coches en espera
                if self.estado != "amarillo":
                    print("Semáforo cambiando a amarillo, no hay coches esperando.")
                self.estado = "amarillo"
                self.color = "yellow"

class Calle(Agent):
    def __init__(self, unique_id, model, tipo="calle"):
        super().__init__(unique_id, model)
        self.tipo = tipo  # tipo de carril, puede ser "calle" o "carril" adicional

class InterseccionModel(Model):
    def __init__(self, ancho, alto, num_normales, num_rapidos, num_lentos, num_desobedientes, num_obstructores):
        self.grid = MultiGrid(ancho, alto, True)
        self.schedule = SimultaneousActivation(self)
        self.running = True

        centro_x = ancho // 2
        centro_y = alto // 2

        # Crear calles y carriles en el centro para formar la intersección
        for x in range(ancho):
            for y in range(alto):
                if (x == centro_x or x == centro_x - 1 or x == centro_x + 1) or (y == centro_y or y == centro_y - 1 or y == centro_y + 1):
                    tipo_carril = "carril" if (x == centro_x - 1 or x == centro_x + 1 or y == centro_y - 1 or y == centro_y + 1) else "calle"
                    calle = Calle(f"calle_{x}_{y}", self, tipo=tipo_carril)
                    self.grid.place_agent(calle, (x, y))

        # Posiciones iniciales para los coches en cada dirección y carril
        posiciones_carril = {
            "norte": [(centro_x - 1, alto - 1), (centro_x, alto - 1), (centro_x + 1, alto - 1)],
            "sur": [(centro_x - 1, 0), (centro_x, 0), (centro_x + 1, 0)],
            "este": [(ancho - 1, centro_y - 1), (ancho - 1, centro_y), (ancho - 1, centro_y + 1)],
            "oeste": [(0, centro_y - 1), (0, centro_y), (0, centro_y + 1)]
        }

        # Destinos permitidos para evitar que regresen al mismo origen
        destinos_permitidos = {
            "norte": ["izquierda", "derecha"],
            "sur": ["izquierda", "derecha"],
            "este": ["arriba", "izquierda"],
            "oeste": ["arriba", "derecha"]
        }

        origenes = list(posiciones_carril.keys())

        # Crear los agentes según los parámetros
        def crear_coches(tipo, cantidad):
            for i in range(cantidad):
                origen = origenes[i % len(origenes)]
                destino = random.choice(destinos_permitidos[origen])
                estado = random.choice(["tranquilo", "enojado"])
                posicion_inicial = posiciones_carril[origen][i % 3]

                if tipo == "normal":
                    coche = CocheNormal(i, self, destino, estado)
                elif tipo == "rapido":
                    coche = CocheRapido(i, self, destino, estado)
                elif tipo == "lento":
                    coche = CocheLento(i, self, destino, estado)
                elif tipo == "desobediente":
                    coche = CocheDesobediente(i, self, destino, estado)
                elif tipo == "obstructor":
                    coche = CocheObstructor(i, self, destino, estado)

                self.grid.place_agent(coche, posicion_inicial)
                self.schedule.add(coche)

        # Crear los agentes en función de los parámetros
        crear_coches("normal", num_normales)
        crear_coches("rapido", num_rapidos)
        crear_coches("lento", num_lentos)
        crear_coches("desobediente", num_desobedientes)
        crear_coches("obstructor", num_obstructores)

        # Crear el semáforo en el centro de la intersección
        self.semaforo = Semaforo("semaforo", self)
        centro = (centro_x, centro_y)
        self.grid.place_agent(self.semaforo, centro)
        self.schedule.add(self.semaforo)

    def step(self):
        self.schedule.step()  # Ejecuta un paso en la simulación
