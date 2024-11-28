# server.py
from flask import Flask, jsonify
from flask_cors import CORS
from model import TrafficModel
from agents import (NormalCarAgent, FastCarAgent, SlowCarAgent, 
                   DisobedientCarAgent, DijkstraCarAgent, TrafficLightAgent, SidewalkAgent)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Crear una única instancia del modelo
model = TrafficModel()

def get_car_direction(pos):
    """Obtiene la dirección del coche basada en su posición actual"""
    direction = model.street_directions.get(pos)
    if isinstance(direction, list):
        return direction[0]
    return direction

@app.route('/positions/cars')
def get_car_positions():
    model.step()  # Avanza un paso
    car_data = []
    for agent in model.schedule.agents:
        if isinstance(agent, (NormalCarAgent, FastCarAgent, SlowCarAgent, 
                           DisobedientCarAgent, DijkstraCarAgent)):
            car_data.append({
                "id": agent.unique_id,
                "type": agent.__class__.__name__,
                "position": agent.pos,
                "state": agent.estado,
                "direction": get_car_direction(agent.pos)
            })
    return jsonify({"data": car_data})

@app.route('/positions/traffic_lights')
def get_traffic_light_positions():
    traffic_light_data = []
    for agent in model.schedule.agents:
        if isinstance(agent, TrafficLightAgent):
            traffic_light_data.append({
                "id": agent.unique_id,
                "position": agent.pos,
                "state": agent.state
            })
    return jsonify({"data": traffic_light_data})

@app.route('/positions/sidewalks')
def get_sidewalk_positions():
    sidewalk_data = []
    for agent in model.schedule.agents:
        if isinstance(agent, SidewalkAgent):
            sidewalk_data.append({
                "id": agent.unique_id,
                "position": agent.pos,
                "state": agent.state()
            })
    return jsonify({"data": sidewalk_data})

if __name__ == '__main__':
    app.run(port=5000, debug=False)