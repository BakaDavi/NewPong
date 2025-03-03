import pyxel
import player
import random
import math


class BallBase:
    def __init__(self, x, y, size):
        self.x_origin = x
        self.y_origin = y
        self.x = x
        self.y = y
        self.width = size
        self.height = size
        
        #self.max_angle = math.radians(75)
        pass               

    # def on_collide(self, collided_object):            
    #     if collided_object.player_type == player.PlayerType.LEFT:
    #         self.x = collided_object.x + collided_object.width + 5
    #     elif collided_object.player_type == player.PlayerType.RIGHT:
    #         self.x = collided_object.x - self.width - 5
    #     relative_intersect = ((self.y + self.height//2) - (collided_object.y + collided_object.height//2)) / (collided_object.height / 2)
    #     angle = relative_intersect * self.max_angle  # `max_angle` is the max deflection in radians
    #     speed = math.sqrt(self.x_vel**2 + self.y_vel**2)  # Keep speed constant
    #     self.x_vel = speed * math.cos(angle) * (-1 if self.x_vel > 0 else 1)
    #     self.y_vel = speed * math.sin(angle)
    
    # def on_out_of_bounds(self, is_upper):
    #     if is_upper:
    #         self.y_vel *= -1
    #         if self.y < pyxel.width // 2:
    #             self.y + 5
    #         else:
    #             self.y - 5
    #     else:
    #         if self.x < pyxel.width // 2:
    #             self.points_manager.add_points_to_player(self.points_manager.player_two)
    #         else:
    #             self.points_manager.add_points_to_player(self.points_manager.player_one)
    #         self.x = pyxel.width // 2 - self.width // 2
    #         self.y = pyxel.height // 2 - self.height // 2
    #         self.x_vel *= -1


    # def tick(self):
    #     self.x = (self.x + self.x_vel)
    #     self.y = (self.y + self.y_vel)        

    def render(self):
        pyxel.rect(self.x,self.y,self.width,self.height,7)
        pass

    def register_to_managers(self, managers):
        for manager in managers:
            manager.register_object(self)

    # def reset(self):
    #     self.x = self.x_origin
    #     self.y = self.y_origin
        # updatables.append(self)
        # drawables.append(self)
        # physic_objects.append(self)