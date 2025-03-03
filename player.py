import pyxel
from enum import Enum

class PlayerType(Enum):
    LEFT = 1
    RIGHT = 2

class PlayerBase:
    def __init__(self, x, y, up, down, name, remote):
        self.x = x
        self.y_origin = y
        self.y = y
        self.up = up
        self.down = down
        self.height = 40
        self.width = 10
        self.name = name
        self.points = 0
        self.position_packet_counter = 0
        self.remote = remote

    def tick(self):
        #move player up and down, unless it results in going out of bounds
        if pyxel.btnp(self.up):
           if self.y > (0):   
              self.y = (self.y - 10) % pyxel.height
              
              
        if pyxel.btnp(self.down):
           if self.y < (pyxel.height - self.height):
               self.y = (self.y + 10) % pyxel.height
        

    def render(self):
        pyxel.rect(self.x,self.y,self.width,self.height,7)

    def render_points(self,x,y):
        pyxel.text(x,y,f"{self.name}: {self.points}",5)

    def register_to_managers(self, managers):
        for manager in managers:
            manager.register_object(self)
    
    def reset(self):
        self.points = 0
        self.y = self.y_origin

    def on_collide(self, obj):
        pass

    def on_out_of_bounds(self, is_upper):
        pass
        
    
class LeftPlayer(PlayerBase):
    def __init__(self, x,y,up_command,down_command, name, remote):
        super().__init__(x,y,up_command,down_command, name, remote)
        self.player_type = PlayerType.LEFT

    def tick(self):
        super().tick()

    def render(self):
        super().render()
        if not self.remote:
            self.render_points(10,10)
    


class RightPlayer(PlayerBase):
    def __init__(self, x,y,up_command,down_command, name, remote):
        super().__init__(x,y,up_command,down_command, name, remote)
        self.player_type = PlayerType.RIGHT

    def tick(self):        
        super().tick()

    def render(self):
        super().render()
        if not self.remote:
            self.render_points(100,10)