import mesa
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from agents import (DijkstraCarAgent,FastCarAgent,SlowCarAgent,DisobedientCarAgent,ObstructorCarAgent, TrafficLightAgent, SidewalkAgent, 
                   BuildingAgent, RoundaboutAgent, ParkingAgent)
from agents import TrafficLightAgent, SidewalkAgent
from agents import BuildingAgent, RoundaboutAgent, StreetAgent




# Modelo principal
class TrafficModel(mesa.Model):
    def __init__(self, width=24, height=24):
        super().__init__()
        self.grid = mesa.space.MultiGrid(width, height, False)
        self.schedule = mesa.time.RandomActivation(self)

        self.street_directions = {}

        # calle larga de abajo, direccion a la derecha
        #carril 1
        for x in range(0,23):  # De 0 a 22
            self.street_directions[(x, 0)] = "right"
        #carril 2
        for x in range(1,22):
            self.street_directions[(x, 1)] = "right"

        # calle larga de la izqueirda, dirección hacia abajo
        #carril 1
        for y in range(1,24):  
            self.street_directions[(0, y)] = "down"
        #carril 2
        for y in range(2,23):
            self.street_directions[(1, y)] = "down"

        # calle larga de la derecha, dirección hacia arriba
        #caril 1
        for y in range(0,24):
            self.street_directions[(23, y)] = "up"
        #carril 2
        for y in range(1,22):
            self.street_directions[(22, y)] = "up"

        # calle larga de arriba, dirección a la izquierda
        #carril 1
        for x in range (1,24):
            self.street_directions[(x, 23)] = "left"
        #carril 2
        for x in range(2,23):
            self.street_directions[(x, 22)] = "left"


        # Calle pequeña entre parking 3 y 5, dirección hacia la izquierda
        #carril 1
        for x in range(2,6):
            self.street_directions[(x, 4)] = "left"
        #carril 2   
        for x in range(2,6):
            self.street_directions[(x, 5)] = "left"

        # Calle pequeña entre parking 11 y 8, dirección hacia la derecha
        #carril 1
        for x in range(8,12):
            self.street_directions[(x, 4)] = "right"
        #carril 2
        for x in range(8,12):
            self.street_directions[(x, 5)] = "right"
        
        # Calle pequeña entre parking 9 y 7, dirección hacia la izquierda PENDIENTEEEE
        #carril 1
        for x in range(8,12): #CAMBIAR 9 POR 8
            self.street_directions[(x, 17)] = "left"
        #carril 2
        for x in range(8,12):
            self.street_directions[(x, 18)] = "left"

        # Calle pequeña del edificio inferior izquierdo, dirección hacia abajo
        #carril 1
        for y in range(2,8):
            self.street_directions[(6, y)] = "down"
        #carril 2
        for y in range(2,8):
            self.street_directions[(7, y)] = "down"

        # Calle pequeña del edificio superior izquierdo, dirección hacia arriba
        #carril 1
        for y in range(12,22):
            self.street_directions[(6, y)] = "up"
        #carril 2
        for y in range(12,22):
            self.street_directions[(7, y)] = "up"
        
        # calle pequeña entre parking 15 y 16, dirección hacia la izquierda
        #carril 1
        for x in range (16,22):
            self.street_directions[(x, 17)] = "left"
        #carril 2
        for x in range (16,22):
            self.street_directions[(x, 16)] = "left"

        # calle central lado izquierdo de la glorieta, dirección hacia la derecha
        #carril 1
        for x in range (2, 12):
            self.street_directions[(x, 8)] = "right"
        #carril 2
        for x in range (2, 12):
            self.street_directions[(x, 9)] = "right"
        
        # calle central lado izquierdo de la glorieta, dirección hacia la izquierda
        #carril 1
        for x in range (2, 12):
            self.street_directions[(x, 11)] = "left"
        #carril 2
        for x in range (2, 12):
            self.street_directions[(x, 10)] = "left"
        
        # calle central lado derecho de la glorieta, dirección hacia la izquierda
        #carril 1
        for x in range(16,22):
            self.street_directions[(x, 11)] = "left"
        #carril 2
        for x in range(16,22):
            self.street_directions[(x, 10)] = "left"
        
        # calle central lado derecho de la glorieta, dirección hacia la derecha
        #carril 1
        for x in range(16,22):
            self.street_directions[(x, 8)] = "right"
        #carril 2
        for x in range(16,22):
            self.street_directions[(x, 9)] = "right"
        
        # calle central lado superior de la glorieta, dirección hacia abajo
        #carril 1
        for y in range(12,22):
            self.street_directions[(12, y)] = "down"
        for y in range(12,22):
            self.street_directions[(13, y)] = "down"
        
        # calle central lado superior de la glorieta, dirección habia arriba
        #carril 1
        for y in range(12,22):
            self.street_directions[(14, y)] = "up"
        for y in range(12,22):
            self.street_directions[(15, y)] = "up"

        
        # calle central lado inferior de la glorieta, dirección hacia arriba
        #carril 1
        for y in range(2,8):
            self.street_directions[(15, y)] = "up"
        #carril 2
        for y in range(2,8):
            self.street_directions[(14, y)] = "up"

        # calle central lado inferior de la glorieta, dirección hacia abajo
        #carril 1
        for y in range(2,8):
            self.street_directions[(12, y)] = "down"
        #carril 2
        for y in range(2,8):
            self.street_directions[(13, y)] = "down"

        # Crear edificios (coordenadas precisas)
        buildings = [
            (2,2,4,2),
            (2,6,4,2),
            (8,2,4,2),
            (8,6,4,2),
            (2,12,4,10),
            (8,12,4,5),
            (8,19,4,3),
            (16,2,2,6),
            (20,2,2,6),
            (16,12,6,4),
            (16,18,6,4)
        ]
        
        # Crear estacionamientos con sus números específicos
        parkings = [
            (3,21,2),
            (5,17,6),
            (2,14,1),
            (4,12,4),
            (4,3,5),
            (3,6,3),
            (9,2,8),
            (10,7,11),
            (8,15,7),
            (10,19,9),
            (10,12,10),
            (17,6,13),
            (17,4,14),
            (20,4,17),
            (20,15,16),
            (20,18,15),
            (17,21,12)
        ]
        
        # En la clase TrafficModel, definimos:
        # (x_semaforo, y_semaforo, ancho_semaforo, x_inicio_sidewalk, y_sidewalk, ancho_sidewalk)
        traffic_light_sidewalks = [
            (5, 0, 2, 6, 2, 2),     # Semáforo izquierdo y su sidewalk
            (2, 4, 2, 0, 6, 2),     # Semáforo inferior y su sidewalk
            (8, 17, 2, 6, 16, 2),       # Semáforo central y su sidewalk
            (8, 22, 2, 6, 21, 2),    # Semáforo derecho y su sidewalk
            (17, 8, 2, 18, 7, 2)
        ]


        
        # Crear glorieta (2x2)
        roundabout = [(13, 9), (14, 9), (13, 10), (14, 10)]
        
        # Colocar edificios
        agent_id = 0
        for x, y, w, h in buildings:
            for i in range(w):
                for j in range(h):
                    if 0 <= x+i < width and 0 <= y+j < height:
                        agent = BuildingAgent(agent_id, self)
                        self.grid.place_agent(agent, (x+i, y+j))
                        self.schedule.add(agent)
                        agent_id += 1
        
        # Colocar estacionamientos
        for x, y, num in parkings:
            agent = ParkingAgent(agent_id, self, num)
            self.grid.place_agent(agent, (x, y))
            self.schedule.add(agent)
            agent_id += 1
        
            
        # Ajuste de colocación de semáforos verticales
        for tl_x, tl_y, tl_height, sw_x, sw_y, sw_width in traffic_light_sidewalks:
            # Crear un único semáforo para esta ubicación
            traffic_light = TrafficLightAgent(agent_id, self)
            self.grid.place_agent(traffic_light, (tl_x, tl_y))  # Posición inicial del semáforo
            self.schedule.add(traffic_light)
            agent_id += 1

            # Colocar el semáforo en posiciones verticales adicionales si es necesario
            for j in range(1, tl_height):
                self.grid.place_agent(traffic_light, (tl_x, tl_y + j))  # Colocar en más celdas si el semáforo es alto

            # Crear y asociar el sidewalk al semáforo
            for i in range(sw_width):
                sidewalk_agent = SidewalkAgent(agent_id, self, traffic_light)  # Asocia al semáforo
                self.grid.place_agent(sidewalk_agent, (sw_x + i, sw_y))  # Posición del sidewalk
                self.schedule.add(sidewalk_agent)
                agent_id += 1


            
        # Colocar glorieta
        for x, y in roundabout:
            agent = RoundaboutAgent(agent_id, self)
            self.grid.place_agent(agent, (x, y))
            self.schedule.add(agent)
            agent_id += 1

        

        # Crear coches normales
        start_positions = [(0,23), (1,22), (2,8), (2,9), (11,11), (11,10), (5,4), (5,5), (8,4), (8,5), (11,18), (11,17), (6,7), (7,7), (6,12), (7,12), (21,11), (21,10), (16,9), (16,8), (21,16), (21,17), (12,21), (13,21), (14,12), (15,12), (15,2), (14,2), (12,7), (13,7)]  # Posiciones iniciales válidas
        # Crear lista de posiciones disponibles
        available_positions = start_positions.copy()

        for pos in start_positions[:15]:
            car = DijkstraCarAgent(self.next_id(), self, pos)
            self.grid.place_agent(car, pos)
            self.schedule.add(car)
            available_positions.remove(pos)

        # Crear coches rápidos
        num_fast_cars = 5
        for _ in range(num_fast_cars):
            if available_positions:
                pos = self.random.choice(available_positions)
                car = FastCarAgent(self.next_id(), self, pos)
                self.grid.place_agent(car, pos)
                self.schedule.add(car)
                available_positions.remove(pos)

        # Crear coches lentos
        num_slow_cars = 5
        for _ in range(num_slow_cars):
            if available_positions:
                pos = self.random.choice(available_positions)
                car = SlowCarAgent(self.next_id(), self, pos)
                self.grid.place_agent(car, pos)
                self.schedule.add(car)
                available_positions.remove(pos)

        # Crear coches desobedientes
        num_disobedient_cars = 3
        for _ in range(num_disobedient_cars):
            if available_positions:
                pos = self.random.choice(available_positions)
                car = DisobedientCarAgent(self.next_id(), self, pos)
                self.grid.place_agent(car, pos)
                self.schedule.add(car)
                available_positions.remove(pos)

        # Crear coches obstructores
        num_obstructor_cars = 2
        for _ in range(num_obstructor_cars):
            if available_positions:
                pos = self.random.choice(available_positions)
                car = ObstructorCarAgent(self.next_id(), self, pos)
                self.grid.place_agent(car, pos)
                self.schedule.add(car)
                available_positions.remove(pos)
                    
    def step(self):
        self.schedule.step()

def agent_portrayal(agent):
    if agent is None:
        return None
        
    portrayal = {"Shape": "rect", "w": 0.9, "h": 0.9, "Filled": "true", "Layer": 0}
    
    if isinstance(agent, BuildingAgent):
        portrayal["Color"] = "#87CEEB"  # Azul claro
        portrayal["Layer"] = 0
    elif isinstance(agent, ParkingAgent):
        portrayal["Color"] = "#FFFF00"  # Amarillo
        portrayal["Layer"] = 1
        portrayal["text"] = str(agent.number)
        portrayal["text_color"] = "black"
    elif isinstance(agent, TrafficLightAgent):
        portrayal["Color"] = "#00FF00" if agent.state == "green" else "#FF0000" # verde o rojo
        portrayal["Layer"] = 2
    elif isinstance(agent, RoundaboutAgent):
        portrayal["Color"] = "#8B4513"  # Marrón
        portrayal["Layer"] = 1
    elif isinstance(agent, SidewalkAgent):
        portrayal["Color"] = "#00FF00" if agent.state() == "green" else "#FF0000"  # Verde o rojo opuesto al trafficlightagent
        portrayal["Layer"] = 1
    # Primero verificar los tipos específicos de coches
    elif isinstance(agent, FastCarAgent):
        portrayal["Color"] = "#FFD700"  # Rojo
        portrayal["Layer"] = 3
    elif isinstance(agent, SlowCarAgent):
        portrayal["Color"] = "#008000"  # Verde oscuro
        portrayal["Layer"] = 3
    elif isinstance(agent, DisobedientCarAgent):
        portrayal["Color"] = "#800080"  # Púrpura
        portrayal["Layer"] = 3
    elif isinstance(agent, ObstructorCarAgent):
        portrayal["Color"] = "#FFA500"  # Naranja
        portrayal["Layer"] = 3
    # NormalCarAgent debe ir al final
    elif isinstance(agent, DijkstraCarAgent):
        portrayal["Color"] = "#0000FF"  # Azul oscuro
        portrayal["Layer"] = 3
        
    return portrayal

# Crear y lanzar el servidor
grid = CanvasGrid(agent_portrayal, 24, 24, 600, 600)  # Aumenté el tamaño para mejor visibilidad
server = ModularServer(TrafficModel, [grid], "Traffic Model", {})
server.port = 8521
server.launch()
