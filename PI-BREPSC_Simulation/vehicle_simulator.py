import pygame
import random
from config import *

class Vehicle:
    def __init__(self, id, start_pos, speed, direction):
        self.id = id
        self.pos = list(start_pos)
        self.speed = speed
        self.direction = direction # "horizontal" or "vertical"
        self.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        self.width = 40
        self.height = 20

    def update_position(self):
        if self.direction == "horizontal":
            self.pos[0] += self.speed
            # Loop vehicle around the screen
            if self.pos[0] > SCREEN_WIDTH:
                self.pos[0] = -self.width
        else:
            self.pos[1] += self.speed
            # Loop vehicle around the screen
            if self.pos[1] > SCREEN_HEIGHT:
                self.pos[1] = -self.height

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (int(self.pos[0]), int(self.pos[1]), self.width, self.height))