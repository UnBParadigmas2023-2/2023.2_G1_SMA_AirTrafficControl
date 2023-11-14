# Import necessary SPADE modules
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.template import Template
from spade.message import Message
import asyncio
import spade
import random
import json
import os


class Environment:
    def __init__(self):
        self.aircraft_positions = {}
        self.weather_conditions = {}
        self.runway_status = {}
        self.airport_positions = {}
        self.conflict_zones = []  # Zonas onde podem ocorrer conflitos

    def generate_airport(self):
        print("Esta cena aqui deu")
        for i in range(5):
            positionX = random.randint(2,38)
            positionY = random.randint(2,28)
            self.airport_positions[i] = (positionX, positionY)
        with open("airport_positions.json", "w") as file:
            print("vou escrever2")
            json.dump(self.airport_positions, file)
            print("escrevi2")

    def update_aircraft_position(self, aircraft_id, position):
        self.aircraft_positions[aircraft_id] = position
        self.detect_conflicts()

    def move_aircraft(self):
        for aircraft_id, position in self.aircraft_positions.items():
            if isinstance(position, tuple) and len(position) == 2:
                new_x = position[0] + random.randint(-10, 10)
                new_y = position[1] + random.randint(-10, 10)
                self.aircraft_positions[aircraft_id] = (new_x, new_y)
            print(f"Moved aircraft {aircraft_id} to position {self.aircraft_positions[aircraft_id]}")
        with open("aircraft_positions.json", "w") as file:
            print("vou escrever")
            json.dump(self.aircraft_positions, file)
            print("escrevi")

    def detect_conflicts(self):
        self.conflict_zones = []
        for id1, pos1 in self.aircraft_positions.items():
            for id2, pos2 in self.aircraft_positions.items():
                if id1 != id2 and self.is_close(pos1, pos2):
                    self.conflict_zones.append((id1, id2))

    def is_close(self, pos1, pos2, min_distance=10):
        # Determinar se duas aeronaves estão perigosamente próximas
        return abs(pos1[0] - pos2[0]) < min_distance and abs(pos1[1] - pos2[1]) < min_distance

    def suggest_routes(self, aircraft_id):
        # Verificar se a aeronave está em uma zona de conflito
        for conflict in self.conflict_zones:
            if aircraft_id in conflict:
                # Gerar uma rota alternativa
                return self.generate_alternative_route(aircraft_id)
        return []

    def generate_alternative_route(self, aircraft_id):
        # Gerar uma rota aleatória como exemplo
        new_x = random.randint(0, 1000)
        new_y = random.randint(0, 1000)
        return (new_x, new_y)

    def update_weather(self, weather_data):
        self.weather_conditions = weather_data

    def update_runway_status(self, runway_id, status):
        self.runway_status[runway_id] = status

    def get_aircraft_positions(self):
        return self.aircraft_positions

    def get_weather_data(self):
        return {"wind": random.choice(["N", "S", "E", "W"]), "visibility": random.choice(["good", "moderate", "poor"])}

    def get_runway_status(self):
        return {"runway1": random.choice(["free", "occupied", "maintenance"])}


class AirTrafficControlAgent(Agent):
    def __init__(self, jid, password, environment):
        super().__init__(jid, password)
        self.environment = environment

    async def setup(self):
        self.add_behaviour(self.EnvironmentInteraction())

    class EnvironmentInteraction(CyclicBehaviour):
        first=False

        async def run(self):
            print("EnvironmentInteraction behavior is running")
            print(self.first)
            if (self.first != True):
                print("aqui")
                # Atualizar a posição das aeronaves
                self.agent.environment.move_aircraft()
                first=True
            # Perceber os dados do ambiente
            aircraft_positions = self.agent.environment.get_aircraft_positions()
            weather_data = self.agent.environment.get_weather_data()
            runway_status = self.agent.environment.get_runway_status()

            # Detectar conflitos
            self.agent.environment.detect_conflicts()

            # Resolver conflitos e comunicar com as aeronaves
            for conflict_zone in self.agent.environment.conflict_zones:
                for aircraft_id in conflict_zone:
                    new_route = self.agent.environment.suggest_routes(aircraft_id)
                    if new_route:
                        await self.send_route_instructions(aircraft_id, new_route)
            

            await asyncio.sleep(2)

        async def send_route_instructions(self, aircraft_id, new_route):
            # Criar uma mensagem ACL
            msg = Message(to=f"airplane{aircraft_id}@localhost")  # Substituir pelo JID correto do agente da aeronave
            msg.set_metadata("performative", "inform")
            msg.set_metadata("language", "English")
            msg.set_metadata("ontology", "AirTrafficControl")

            # Incluir as instruções de rota na mensagem
            msg.body = f"New route instructions: {new_route}"

            # Enviar a mensagem
            await self.send(msg)
            print(f"Sent new route to aircraft {aircraft_id}: {new_route}")



class AircraftAgent(Agent):
    def __init__(self, jid, password, environment, pos):
        super().__init__(jid, password)
        self.environment = environment
        self.id = self.extract_id(jid)
        self.position = pos
        self.environment.update_aircraft_position(self.id, pos)

    def extract_id(self, jid):
        # Extrair o ID do JID do agente
        parts = jid.split("@")[0].split("e")
        return int(parts[1]) if len(parts) > 1 else 0

    async def setup(self):
        self.add_behaviour(self.AircraftInteraction())

    class AircraftInteraction(CyclicBehaviour):
        async def run(self):
            # Atualizar a posição da aeronave
            self.agent.update_position()

            # Comunicar posição atual para o ATC
            await self.send_instruction_to_atc(self.agent.position)

            # Aguardar instruções de rota do ATC
            await self.receive_route_instructions()

            await asyncio.sleep(3)

        async def send_instruction_to_atc(self, position):
            # Enviar posição atual para o ATC
            msg = Message(to="atc_agent@localhost")
            msg.set_metadata("performative", "inform")
            msg.body = f"Aircraft {self.agent.id} at position {position} requesting instructions."
            await self.send(msg)

        async def receive_route_instructions(self):
            # Receber instruções de rota do ATC
            msg = await self.receive(timeout=1)  # Esperar por uma mensagem por um tempo limite
            if msg:
                new_route = msg.body
                print(f"Received new route instructions: {new_route}")
                # Atualizar a rota da aeronave conforme necessário

    def update_position(self):
        # Atualizar a posição da aeronave no ambiente
        new_x = random.randint(0, 1000)
        new_y = random.randint(0, 1000)
        self.position = (new_x, new_y)
        self.environment.update_aircraft_position(self.id, self.position)

async def main():
    # Inicializar o ambiente
    atc_environment = Environment()
    atc_environment.generate_airport()

    for airport in atc_environment.airport_positions:
        print(airport)

    # Verificar e criar o arquivo de posições dos aeroportos, se necessário
    if not os.path.exists("airport_positions.json"):
        with open("airport_positions.json", "w") as file:
            json.dump({}, file)

    # Verificar e criar o arquivo de posições dos aviões, se necessário
    if not os.path.exists("aircraft_positions.json"):
        with open("aircraft_positions.json", "w") as file:
            json.dump({}, file)

    # Inicializar e iniciar o agente de controle de tráfego aéreo
    atc_agent = AirTrafficControlAgent("atc_agent@localhost", "password", atc_environment)
    await atc_agent.start(auto_register=True)

    # Inicializar e iniciar os agentes de aeronaves
    aircraft_agents = []
    for i in range(5):
        pos = (random.randint(0, 100), random.randint(0, 100))
        agent = AircraftAgent(f"airplane{i}@localhost", "password", atc_environment, pos)
        aircraft_agents.append(agent)
        await agent.start(auto_register=True)

    # Loop principal
    while True:
        await asyncio.sleep(1)  # Intervalo de atualização

if __name__ == "__main__":
    spade.run(main())