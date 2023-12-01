from mesa import Agent
from random import choice, randint

class Airplane(Agent):
    def __init__(self, unique_id, model, origin : list ,destination : list):
        super().__init__(unique_id, model)
        self.destination = destination
        self.origin = origin
        self.heading_x = 1
        self.heading_y = 0

    def step(self):
        self.move()

    def get_direction(self):
        return [self.heading_x, self.heading_y]

    def move(self):
        if self.origin == self.destination:
            print("Airplane has arrived at destination")
            now = self.model.schedule.steps
            while not self.model.schedule.steps < now + randint(0, 1000):
                self.model.schedule.steps
                print(self.model.schedule.steps)
            self.destination[0], self.destination[1] = choice(self.model.get_airports())

        x0 = self.origin[0]
        y0 = self.origin[1]
        x1 = self.destination[0]
        y1 = self.destination[1]

        if [x0,y0] != [x1,y1]:
            if x0 < x1:
                x0 = x0 + 1
                self.heading_x = 1
                self.heading_y = 0
            elif x0 > x1 :
                x0 = x0 - 1
                self.heading_x = -1
                self.heading_y = 0
            elif y0 < y1:
                y0 = y0 + 1
                self.heading_x = 0
                self.heading_y = 1
            elif y0 > y1:
                y0 = y0 - 1
                self.heading_x = 0
                self.heading_y = -1
        self.model.grid.move_agent(self, (x0,y0))

        self.origin[0] = x0
        self.origin[1] = y0
        self.destination[0] = x1
        self.destination[1] = y1

class Airport(Agent):
    def __init__(self, unique_id, model, pos):
        super().__init__(unique_id, model)
        self.pos = pos

    def step(self):
        # Aeroportos são agentes fixos, não têm movimento
        pass
