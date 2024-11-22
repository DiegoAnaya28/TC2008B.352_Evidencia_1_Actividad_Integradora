import random
import mesa


class NormalCarAgent(mesa.Agent):
    def __init__(self, unique_id, model, start_pos):
        super().__init__(unique_id, model)
        self.pos = start_pos  # Posición inicial del coche
        self.parked = False   # Indica si el coche ya encontró un estacionamiento

    def move(self):
        if self.parked:
            return  # Si está estacionado, no se mueve

        # Obtener la dirección permitida para la posición actual
        direction = self.model.street_directions.get(self.pos)
        print(f"Coche en {self.pos}, dirección permitida: {direction}")

        # Determinar la próxima posición basada en la dirección
        next_pos = None
        if direction == "right":
            next_pos = (self.pos[0] + 1, self.pos[1])
        elif direction == "left":
            next_pos = (self.pos[0] - 1, self.pos[1])
        elif direction == "up":
            next_pos = (self.pos[0], self.pos[1] + 1)
        elif direction == "down":
            next_pos = (self.pos[0], self.pos[1] - 1)

        # Validar que la próxima posición sea válida, diferente de la actual, y esté en street_directions
        if next_pos and next_pos != self.pos and next_pos in self.model.street_directions:
            # Verificar si la próxima celda contiene un ParkingAgent disponible
            cell_contents = self.model.grid.get_cell_list_contents([next_pos])
            is_obstructed = False  # Indicador de si la celda está bloqueada

            for agent in cell_contents:
                # Si hay un semáforo y está en rojo, no se mueve
                if isinstance(agent, TrafficLightAgent) and agent.state == "red":
                    print(f"Semáforo en {next_pos} está rojo. No hay movimiento.")
                    is_obstructed = True
                    break
                # Si hay una acera vinculada a un semáforo en rojo, no se mueve
                if isinstance(agent, SidewalkAgent) and agent.state() == "red":
                    print(f"Sidewalk en {next_pos} asociado a semáforo rojo. No hay movimiento.")
                    is_obstructed = True
                    break
                # Si hay otro coche o un agente que no es un semáforo/acera, está obstruido
                if not isinstance(agent, (TrafficLightAgent, SidewalkAgent)):
                    print(f"La celda {next_pos} está ocupada por {type(agent).__name__}. No hay movimiento.")
                    is_obstructed = True
                    break

            if not is_obstructed:
                # Verificar si la próxima celda contiene un ParkingAgent disponible
                for agent in cell_contents:
                    if isinstance(agent, ParkingAgent) and not agent.occupied:
                        self.park(agent)  # Estacionarse en el ParkingAgent
                        return

                # Si la celda no está obstruida, moverse
                self.model.grid.move_agent(self, next_pos)
                self.pos = next_pos
                print(f"Coche {self.unique_id} se movió a {next_pos}.")
        else:
            print(f"Movimiento inválido desde {self.pos} hacia {next_pos}. Revisión de dirección necesaria.")

    def park(self, parking_agent):
        self.parked = True
        parking_agent.occupied = True  # Marcar el estacionamiento como ocupado
        print(f"Coche {self.unique_id} estacionado en {self.pos}.")

    def step(self):
        self.move()


class FastCarAgent(NormalCarAgent):
    def __init__(self, unique_id, model, start_pos):
        super().__init__(unique_id, model, start_pos)
        self.speed = 2  # Se mueve 2 celdas por paso
        
    def move(self):
        # Realiza el movimiento normal dos veces por paso
        for _ in range(self.speed):
            if not self.parked:
                super().move()

class SlowCarAgent(NormalCarAgent):
    def __init__(self, unique_id, model, start_pos):
        super().__init__(unique_id, model, start_pos)
        self.speed = 0.5  # Se mueve cada dos pasos
        self.step_counter = 0
        
    def step(self):
        self.step_counter += 1
        if self.step_counter >= 2:  # Solo se mueve cada dos pasos
            self.move()
            self.step_counter = 0

class DisobedientCarAgent(NormalCarAgent):
    def __init__(self, unique_id, model, start_pos):
        super().__init__(unique_id, model, start_pos)
        self.disobedient = True
        
    def move(self):
        if self.parked:
            return
            
        direction = self.model.street_directions.get(self.pos)
        next_pos = None
        
        # Calcula la siguiente posición igual que NormalCarAgent
        if direction == "right":
            next_pos = (self.pos[0] + 1, self.pos[1])
        elif direction == "left":
            next_pos = (self.pos[0] - 1, self.pos[1])
        elif direction == "up":
            next_pos = (self.pos[0], self.pos[1] + 1)
        elif direction == "down":
            next_pos = (self.pos[0], self.pos[1] - 1)
            
        if next_pos and next_pos != self.pos and next_pos in self.model.street_directions:
            # Ignora semáforos en rojo con 50% de probabilidad
            cell_contents = self.model.grid.get_cell_list_contents([next_pos])
            can_move = True
            
            for agent in cell_contents:
                if isinstance(agent, TrafficLightAgent) and agent.state == "red":
                    if random.random() > 0.5:  # 50% de probabilidad de ignorar el semáforo
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
        self.obstruct_time = 5  # Tiempo que permanece obstruyendo
        
    def step(self):
        if not self.parked:
            if self.obstruct_counter < self.obstruct_time:
                # Se queda quieto obstruyendo
                self.obstruct_counter += 1
                print(f"Coche obstructor {self.unique_id} bloqueando en {self.pos}")
            else:
                # Después de obstruir, se mueve normalmente
                self.move()


class ParkingAgent(mesa.Agent):
    def __init__(self, unique_id, model, number):
        super().__init__(unique_id, model)
        self.number = number  # Número identificador del estacionamiento
        self.occupied = False  # Estado inicial del estacionamiento



class TrafficLightAgent(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.type = "traffic_light"
        self.state = "red"  # Estado inicial del semáforo
        self.timer = 0  # Temporizador para cambiar el estado del semáforo

    def toggle_state(self):
        # alternar entre rojo y verde
        if self.state == "red":
            self.state = "green"
        else:
            self.state = "red"

    def step(self):
        self.timer += 1
        if self.timer >= 10:   #Cambia el estado cada 10 pasos
            self.toggle_state()
            self.timer = 0

        

class SidewalkAgent(mesa.Agent):
    def __init__(self, unique_id, model, linked_traffic_light):
        super().__init__(unique_id, model)
        self.type = "sidewalk"
        self.linked_traffic_light = linked_traffic_light  # Semáforo asociado
    
    def state(self):
        return "green" if self.linked_traffic_light.state == "red" else "red"
    
    def step(self):
        pass





# Definición de agentes
class BuildingAgent(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.type = "building"
        

class RoundaboutAgent(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.type = "roundabout"

class StreetAgent(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.type = "street"