import random
import mesa

import networkx as nx

class StreetGraph:
    def __init__(self, model):
        self.graph = nx.DiGraph()  # Cambiado a DiGraph para respetar direcciones
        self.model = model
        self.build_graph()
    
    def build_graph(self):
        # Añadir todas las celdas de calle como nodos
        for pos, direction in self.model.street_directions.items():
            self.graph.add_node(pos)
            
            # Añadir aristas según la dirección permitida
            x, y = pos
            if direction == "right" and (x+1, y) in self.model.street_directions:
                self.graph.add_edge(pos, (x+1, y), weight=1)
            elif direction == "left" and (x-1, y) in self.model.street_directions:
                self.graph.add_edge(pos, (x-1, y), weight=1)
            elif direction == "up" and (x, y+1) in self.model.street_directions:
                self.graph.add_edge(pos, (x, y+1), weight=1)
            elif direction == "down" and (x, y-1) in self.model.street_directions:
                self.graph.add_edge(pos, (x, y-1), weight=1)
        
        # Añadir conexiones con estacionamientos
        for agent in self.model.schedule.agents:
            if isinstance(agent, ParkingAgent):
                self.graph.add_node(agent.pos)
                # Conectar con celdas de calle adyacentes
                x, y = agent.pos
                neighbors = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
                for neighbor in neighbors:
                    if neighbor in self.model.street_directions:
                        self.graph.add_edge(neighbor, agent.pos, weight=1)
    
    def find_shortest_path(self, start, parking_spots):
        min_path = None
        min_distance = float('inf')
        
        for parking_spot in parking_spots:
            try:
                path = nx.shortest_path(self.graph, start, parking_spot, weight='weight')
                distance = len(path) - 1
                
                if distance < min_distance:
                    min_distance = distance
                    min_path = path
            except nx.NetworkXNoPath:
                continue
        
        return min_path, min_distance


class NormalCarAgent(mesa.Agent):
    def __init__(self, unique_id, model, start_pos):
        super().__init__(unique_id, model)
        self.pos = start_pos
        self.parked = False
        self.estado = "tranquilo"
        self.tiempo_espera = 0

    def check_available_parkings(self):
        """Cuenta estacionamientos disponibles"""
        available = sum(
            1 for agent in self.model.schedule.agents
            if isinstance(agent, ParkingAgent) and not agent.occupied
        )
        return available

    def adjust_behavior(self):
        """Ajusta comportamiento según disponibilidad"""
        available_parkings = self.check_available_parkings()
        if available_parkings < 5:
            if isinstance(self, FastCarAgent):
                self.speed = 3
            elif isinstance(self, SlowCarAgent):
                self.step_counter = 1
            elif isinstance(self, DijkstraCarAgent):
                self.detection_radius = 2

    def move(self):
        self.adjust_behavior()
        if self.parked:
            return
        
        # Obtener direcciones permitidas
        directions = self.model.street_directions.get(self.pos)
        print(f"Coche en {self.pos}, direcciones permitidas: {directions}")

        if not directions:
            print(f"Coche en {self.pos} no tiene dirección válida. Revisar configuración del modelo.")
            return

        # Si hay varias opciones, elegir aleatoriamente entre las direcciones permitidas
        if isinstance(directions, list):
            direction = self.random.choice(directions)
        else:
            direction = directions

        # Generar la próxima posición basada en la dirección elegida
        next_pos = None
        if direction == "right":
            next_pos = (self.pos[0] + 1, self.pos[1])
        elif direction == "left":
            next_pos = (self.pos[0] - 1, self.pos[1])
        elif direction == "up":
            next_pos = (self.pos[0], self.pos[1] + 1)
        elif direction == "down":
            next_pos = (self.pos[0], self.pos[1] - 1)

        # Validar la próxima posición
        if next_pos and next_pos in self.model.street_directions:
            cell_contents = self.model.grid.get_cell_list_contents([next_pos])
            is_obstructed = False

            for agent in cell_contents:
                if isinstance(agent, TrafficLightAgent) and agent.state == "red":
                    print(f"Semáforo en {next_pos} está rojo. No hay movimiento.")
                    is_obstructed = True
                    self.tiempo_espera += 1
                    if self.tiempo_espera > 3:
                        self.estado = "enojado"
                    break

                if isinstance(agent, SidewalkAgent) and agent.state() == "red":
                    print(f"Sidewalk en {next_pos} asociado a semáforo rojo. No hay movimiento.")
                    is_obstructed = True
                    self.tiempo_espera += 1
                    if self.tiempo_espera > 3:
                        self.estado = "enojado"
                    break

                if isinstance(agent, ParkingAgent) and not agent.occupied:
                    # Intentar estacionarse
                    self.park(agent)
                    return

                if not isinstance(agent, (TrafficLightAgent, SidewalkAgent, ParkingAgent)):
                    print(f"La celda {next_pos} está ocupada por {type(agent).__name__}. No hay movimiento.")
                    is_obstructed = True
                    self.tiempo_espera += 1
                    if self.tiempo_espera > 3:
                        self.estado = "enojado"
                    break

            if not is_obstructed:
                self.tiempo_espera = 0
                self.estado = "tranquilo"
                self.model.grid.move_agent(self, next_pos)
                self.pos = next_pos
                print(f"Coche {self.unique_id} se movió a {next_pos}.")
        else:
            print(f"Movimiento inválido desde {self.pos} hacia {next_pos}. Revisión de dirección necesaria.")
            self.tiempo_espera += 1
            if self.tiempo_espera > 3:
                self.estado = "enojado"

    def park(self, parking_agent):
        """Mover al coche al ParkingAgent y marcarlo como estacionado."""
        if parking_agent.pos == self.pos:
            # Si ya está en la posición del parking, estacionar
            self.parked = True
            parking_agent.occupied = True
            print(f"Coche {self.unique_id} estacionado en {self.pos}.")
        else:
            # Moverse a la posición del parking
            self.model.grid.move_agent(self, parking_agent.pos)
            self.pos = parking_agent.pos
            self.parked = True
            parking_agent.occupied = True
            print(f"Coche {self.unique_id} ingresó y estacionó en {self.pos}.")



    def explore(self):
        """Método para explorar aleatoriamente direcciones válidas."""
        valid_moves = []
        x, y = self.pos

        # Verificar las cuatro direcciones posibles
        possible_moves = {
            "right": (x + 1, y),
            "left": (x - 1, y),
            "up": (x, y + 1),
            "down": (x, y - 1),
        }

        for direction, next_pos in possible_moves.items():
            if next_pos in self.model.street_directions and self.model.street_directions[next_pos] == direction:
                valid_moves.append(next_pos)

        if valid_moves:
            # Elegir una posición válida al azar para "divagar"
            next_pos = self.random.choice(valid_moves)
            self.model.grid.move_agent(self, next_pos)
            self.pos = next_pos
            print(f"Coche {self.unique_id} exploró y se movió a {next_pos}.")

    def change_lane(self):
        """Cambiar de carril hacia uno adyacente que sea válido y disponible."""
        x, y = self.pos
        direction = self.model.street_directions.get(self.pos)
        
        # Definir posiciones adyacentes (horizontales y verticales)
        adjacent_positions = [
            (x + 1, y),  # Derecha
            (x - 1, y),  # Izquierda
            (x, y + 1),  # Arriba
            (x, y - 1),  # Abajo
        ]
        
        for adj_pos in adjacent_positions:
            # Verificar que el carril sea válido y respete las reglas del modelo
            if adj_pos in self.model.street_directions:
                adj_direction = self.model.street_directions.get(adj_pos)
                
                # Verificar si es un carril permitido para cambiar
                if isinstance(direction, list) and adj_direction in direction:
                    cell_contents = self.model.grid.get_cell_list_contents([adj_pos])
                    if not any(isinstance(agent, NormalCarAgent) for agent in cell_contents):
                        self.model.grid.move_agent(self, adj_pos)
                        self.pos = adj_pos
                        print(f"Coche {self.unique_id} cambió de carril a {adj_pos}.")
                        return
                
                # Verificar si el carril tiene la misma dirección que el actual
                if adj_direction == direction:
                    cell_contents = self.model.grid.get_cell_list_contents([adj_pos])
                    if not any(isinstance(agent, NormalCarAgent) for agent in cell_contents):
                        self.model.grid.move_agent(self, adj_pos)
                        self.pos = adj_pos
                        print(f"Coche {self.unique_id} cambió de carril a {adj_pos}.")
                        return
        print(f"Coche {self.unique_id} no encontró un carril disponible para cambiar desde {self.pos}.")



    def step(self):

        # Cambiar de carril si está enojado
        if self.estado == "enojado":
            self.change_lane()
        self.move()

class DijkstraCarAgent(NormalCarAgent):
    def __init__(self, unique_id, model, start_pos):
        super().__init__(unique_id, model, start_pos)
        self.path_to_parking = None
        self.detection_radius = 3  # Detectar estacionamientos a 3 cuadros de distancia
        self.estado = "tranquilo"
        self.tiempo_espera = 0

    def detect_parking_spots(self):
        # Buscar vecinos dentro del radio de detección
        neighbors = self.model.grid.iter_neighbors(self.pos, moore=False, radius=self.detection_radius)
        parking_spots = [
            agent.pos for agent in neighbors
            if isinstance(agent, ParkingAgent) and not agent.occupied
        ]
        return parking_spots

    def move(self):
        if self.parked:
            return
        
        # Detectar estacionamientos dentro del rango
        parking_spots = self.detect_parking_spots()

        if parking_spots and not self.path_to_parking:
            # Si hay estacionamientos en el rango, usar Dijkstra para calcular el camino
            street_graph = StreetGraph(self.model)
            path, _ = street_graph.find_shortest_path(self.pos, parking_spots)
            if path:
                self.path_to_parking = path[1:]  # Guardar el camino
                print(f"Coche {self.unique_id} detectó estacionamientos y calculó un camino: {self.path_to_parking}")
            else:
                print(f"Coche {self.unique_id} no encontró un camino válido hacia estacionamientos.")
                super().move()  # Si no hay camino, moverse normalmente
                return
        elif not parking_spots and not self.path_to_parking:
            # Si no hay estacionamientos cerca, moverse normalmente
            super().move()
            return

        # Movimiento por el camino asignado
        if self.path_to_parking:
            next_pos = self.path_to_parking[0]
            
            # Standard movement checks
            cell_contents = self.model.grid.get_cell_list_contents([next_pos])
            is_obstructed = any(
                isinstance(agent, (TrafficLightAgent, SidewalkAgent))
                and (
                    (isinstance(agent, TrafficLightAgent) and agent.state == "red") or
                    (isinstance(agent, SidewalkAgent) and agent.state() == "red")
                )
                for agent in cell_contents
            ) or any(
                isinstance(agent, (NormalCarAgent, FastCarAgent, SlowCarAgent, 
                                 DisobedientCarAgent))
                for agent in cell_contents
            )
            
            if not is_obstructed:
                self.tiempo_espera = 0
                self.estado = "tranquilo"
                next_pos = self.path_to_parking.pop(0)
                
                # Check for parking at destination
                for agent in cell_contents:
                    if isinstance(agent, ParkingAgent) and not agent.occupied:
                        self.park(agent)
                        self.path_to_parking = None
                        return
                
                # Move to next position
                self.model.grid.move_agent(self, next_pos)
                self.pos = next_pos
                print(f"Coche Dijkstra {self.unique_id} se movió a {next_pos}")
            else:
                self.tiempo_espera += 1
                if self.tiempo_espera > 3:
                    self.estado = "enojado"
                print(f"Coche Dijkstra {self.unique_id} bloqueado en {self.pos}")
        else:
            super().move()


    def step(self):
        # Cambiar de carril si está enojado
        if self.estado == "enojado":
            self.change_lane()
        # Continuar con su movimiento normal
        self.move()
            
class FastCarAgent(DijkstraCarAgent):  # Cambiado a heredar de DijkstraCarAgent
    def __init__(self, unique_id, model, start_pos):
        super().__init__(unique_id, model, start_pos)
        self.speed = 2
        self.estado = "tranquilo"


    def move(self):
        if self.tiempo_espera > 2:  # Se enoja más rápido
            self.estado = "enojado"
        
        for _ in range(self.speed):  # Se mueve dos veces en cada paso
            if not self.parked:
                super().move()


class SlowCarAgent(DijkstraCarAgent):  # Cambiado a heredar de DijkstraCarAgent
    def __init__(self, unique_id, model, start_pos):
        super().__init__(unique_id, model, start_pos)
        self.step_counter = 0
        self.estado = "tranquilo"

    def step(self):
        self.step_counter += 1
        if self.step_counter >= 2:  # Se mueve cada dos pasos
            if not self.parked:
                self.move()
            self.step_counter = 0
        if self.tiempo_espera > 5:  # Más tolerante
            self.estado = "enojado"
        # Cambiar de carril si está enojado
        if self.estado == "enojado":
            self.change_lane()
        
        # Cambiar de carril si está enojado
        if self.estado == "enojado":
            self.change_lane()



class DisobedientCarAgent(DijkstraCarAgent):
    def __init__(self, unique_id, model, start_pos):
        super().__init__(unique_id, model, start_pos)
        self.estado = "enojado"  # Siempre enojado

    def move(self):
        if self.parked:
            return

        direction = self.model.street_directions.get(self.pos)
        next_pos = None

        if direction == "right":
            next_pos = (self.pos[0] + 1, self.pos[1])
        elif direction == "left":
            next_pos = (self.pos[0] - 1, self.pos[1])
        elif direction == "up":
            next_pos = (self.pos[0], self.pos[1] + 1)
        elif direction == "down":
            next_pos = (self.pos[0], self.pos[1] - 1)

        if next_pos and next_pos in self.model.street_directions:
            cell_contents = self.model.grid.get_cell_list_contents([next_pos])
            can_move = True

            for agent in cell_contents:
                # Ignorar semáforo con probabilidad
                if isinstance(agent, TrafficLightAgent) and agent.state == "red":
                    if random.random() > 0.5:  # 50% de ignorar semáforo
                        print(f"Coche desobediente {self.unique_id} ignora el semáforo en {next_pos}")
                        continue
                    else:
                        can_move = False
                        break

                # Restricción para no pasar encima de otros coches
                if isinstance(agent, NormalCarAgent) or isinstance(agent, DijkstraCarAgent) or isinstance(agent, FastCarAgent) or isinstance(agent, SlowCarAgent):
                    print(f"Coche desobediente {self.unique_id} bloqueado por otro coche en {next_pos}")
                    can_move = False
                    break

            if can_move:
                self.model.grid.move_agent(self, next_pos)
                self.pos = next_pos
                print(f"Coche desobediente {self.unique_id} se movió a {next_pos}")
            else:
                print(f"Coche desobediente {self.unique_id} no pudo moverse a {next_pos}")

    def step(self):
        # Siempre cambiar de carril porque está enojado
        self.change_lane()
        # Continuar con su movimiento normal
        self.move()


                    
class ParkingAgent(mesa.Agent):
    def __init__(self, unique_id, model, number):
        super().__init__(unique_id, model)
        self.number = number
        self.occupied = False

class TrafficLightAgent(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.state = "red"
        self.timer = 0

    def toggle_state(self):
        if self.state == "red":
            self.state = "green"
        else:
            self.state = "red"

    def step(self):
        self.timer += 1
        if self.timer >= 10:
            self.toggle_state()
            self.timer = 0

class SidewalkAgent(mesa.Agent):
    def __init__(self, unique_id, model, linked_traffic_light):
        super().__init__(unique_id, model)
        self.linked_traffic_light = linked_traffic_light

    def state(self):
        return "green" if self.linked_traffic_light.state == "red" else "red"

    def step(self):
        pass

class BuildingAgent(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

class RoundaboutAgent(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

class StreetAgent(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
