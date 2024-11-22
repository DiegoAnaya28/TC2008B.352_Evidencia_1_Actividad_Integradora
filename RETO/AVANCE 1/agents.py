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

    def move(self):
        if self.parked:
            return

        direction = self.model.street_directions.get(self.pos)
        print(f"Coche en {self.pos}, dirección permitida: {direction}")

        next_pos = None
        if direction == "right":
            next_pos = (self.pos[0] + 1, self.pos[1])
        elif direction == "left":
            next_pos = (self.pos[0] - 1, self.pos[1])
        elif direction == "up":
            next_pos = (self.pos[0], self.pos[1] + 1)
        elif direction == "down":
            next_pos = (self.pos[0], self.pos[1] - 1)

        if next_pos and next_pos != self.pos and next_pos in self.model.street_directions:
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

                if not isinstance(agent, (TrafficLightAgent, SidewalkAgent)):
                    print(f"La celda {next_pos} está ocupada por {type(agent).__name__}. No hay movimiento.")
                    is_obstructed = True
                    self.tiempo_espera += 1
                    if self.tiempo_espera > 3:
                        self.estado = "enojado"
                    break

            if not is_obstructed:
                self.tiempo_espera = 0
                self.estado = "tranquilo"

                for agent in cell_contents:
                    if isinstance(agent, ParkingAgent) and not agent.occupied:
                        self.park(agent)
                        return

                self.model.grid.move_agent(self, next_pos)
                self.pos = next_pos
                print(f"Coche {self.unique_id} se movió a {next_pos}.")
        else:
            print(f"Movimiento inválido desde {self.pos} hacia {next_pos}. Revisión de dirección necesaria.")
            self.tiempo_espera += 1
            if self.tiempo_espera > 3:
                self.estado = "enojado"

    def park(self, parking_agent):
        self.parked = True
        parking_agent.occupied = True
        print(f"Coche {self.unique_id} estacionado en {self.pos}.")

    def step(self):
        self.move()

class DijkstraCarAgent(NormalCarAgent):
    def __init__(self, unique_id, model, start_pos):
        super().__init__(unique_id, model, start_pos)
        self.path_to_parking = None
        self.estado = "tranquilo"
        self.tiempo_espera = 0

    def move(self):
        if self.parked:
            return

        # Find parking spots if no path exists
        if not self.path_to_parking:
            street_graph = StreetGraph(self.model)
            
            # Find available parking spots
            parking_spots = [
                agent.pos for agent in self.model.schedule.agents
                if isinstance(agent, ParkingAgent) and not agent.occupied
            ]
            
            if not parking_spots:
                print(f"No hay estacionamientos disponibles para el coche Dijkstra {self.unique_id}")
                super().move()
                return
            
            try:
                path, _ = street_graph.find_shortest_path(self.pos, parking_spots)
                if path:
                    self.path_to_parking = path[1:]  # Skip current position
                    print(f"Coche Dijkstra {self.unique_id} encontró camino: {self.path_to_parking}")
                else:
                    print(f"No se encontró camino para el coche Dijkstra {self.unique_id}")
                    super().move()
                    return
            except Exception as e:
                print(f"Error encontrando camino para coche Dijkstra {self.unique_id}: {e}")
                super().move()
                return

        # Move along the path
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
                                 DisobedientCarAgent, ObstructorCarAgent))
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
            
class FastCarAgent(NormalCarAgent):
    def __init__(self, unique_id, model, start_pos):
        super().__init__(unique_id, model, start_pos)
        self.speed = 2
        self.estado = "tranquilo"

    def move(self):
        if self.tiempo_espera > 2:  # Se enoja más rápido
            self.estado = "enojado"
        for _ in range(self.speed):
            if not self.parked:
                super().move()

class SlowCarAgent(NormalCarAgent):
    def __init__(self, unique_id, model, start_pos):
        super().__init__(unique_id, model, start_pos)
        self.step_counter = 0
        self.estado = "tranquilo"

    def step(self):
        self.step_counter += 1
        if self.step_counter >= 2:
            if not self.parked:
                self.move()
            self.step_counter = 0
        if self.tiempo_espera > 5:  # Más tolerante
            self.estado = "enojado"

class DisobedientCarAgent(NormalCarAgent):
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
                if isinstance(agent, TrafficLightAgent) and agent.state == "red":
                    if random.random() > 0.5:  # 50% de ignorar semáforo
                        print(f"Coche desobediente {self.unique_id} ignora el semáforo en {next_pos}")
                        continue
                    else:
                        can_move = False
                        break

            if can_move:
                self.model.grid.move_agent(self, next_pos)
                self.pos = next_pos

class ObstructorCarAgent(NormalCarAgent):
    def __init__(self, unique_id, model, start_pos):
        super().__init__(unique_id, model, start_pos)
        self.obstruct_counter = 0
        self.obstruct_time = 5
        self.estado = "enojado"  # Comienza enojado

    def step(self):
        if not self.parked:
            if self.obstruct_counter < self.obstruct_time:
                self.obstruct_counter += 1
                print(f"Coche obstructor {self.unique_id} bloqueando en {self.pos}")
            else:
                self.move()
                if self.tiempo_espera > 3:
                    self.estado = "enojado"
                else:
                    self.estado = "tranquilo"

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
