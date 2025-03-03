import pyxel

class BaseManager:
    def __init__(self):
        self.managed_objects = []

    def manage(self):
        pass

    def register_object(self,object):
        self.managed_objects.append(object)

class PhysicsManager(BaseManager):
    def __init__(self):
        super().__init__()
        #self.players = players    

    def manage(self):
        # for obj in self.managed_objects:
        #     obj.check_collisions(self.players)

        num_managed_objs = len(self.managed_objects)
        
        #TODO: optimizations to reduce for loop
        for index_one in range(0,num_managed_objs):
            self.check_borders(self.managed_objects[index_one])
            for index_two in range(0,num_managed_objs):
                if index_one != index_two:
                    if self.check_collisions(self.managed_objects[index_one],self.managed_objects[index_two]):
                        self.managed_objects[index_one].on_collide(self.managed_objects[index_two])
                        self.managed_objects[index_two].on_collide(self.managed_objects[index_one])

    def check_collisions(self, obj1, obj2):
        obj1_half_width = obj1.width // 2
        obj2_half_width = obj2.width // 2
        obj1_half_height = obj1.height // 2
        obj2_half_height = obj2.height // 2
        obj1_pivot = (obj1.x + obj1_half_width, obj1.y + obj1_half_height)
        obj2_pivot = (obj2.x + obj2_half_width, obj2.y + obj2_half_height)
        #colliding = obj2_pivot[0] < pyxel.width//2 - 20 and obj2_pivot[0] <= obj1_pivot[0] + halfWidth or obj2_pivot[0] > pyxel.width//2 + 20 and obj2_pivot[0] >= obj1_pivot[0] - halfWidth
        x_collision = obj1_pivot[0] - obj1_half_width < obj2_pivot[0] - obj2_half_width and obj1_pivot[0] + obj1_half_width > obj2_pivot[0] - obj2_half_width or obj1_pivot[0] + obj1_half_width > obj2_pivot[0] + obj2_half_width and obj1_pivot[0] - obj1_half_width < obj2_pivot[0] + obj2_half_width
        y_collision = obj1_pivot[1] + obj1_half_height > obj2_pivot[1] + obj2_half_height and obj1_pivot[1] - obj1_half_height < obj2_pivot[1] + obj2_half_height or obj1_pivot[1] + obj1_half_height > obj2_pivot[1] - obj2_half_height and obj1_pivot[1] - obj1_half_height < obj2_pivot[1] - obj2_half_height
        return x_collision and y_collision
    
    def check_borders(self, obj):    
        if obj.y >= pyxel.height - obj.height or obj.y <= 0:
            obj.on_out_of_bounds(True) 
        if obj.x >= pyxel.width - obj.width or obj.x <= 0:
            obj.on_out_of_bounds(False)
        #check if obj1 collides with obj2 -> AABBSat
        # return True or False
        pass        


class TickManager(BaseManager):
    def __init__(self):
        super().__init__()

    def manage(self):
        for obj in self.managed_objects:
            obj.tick()

class RenderManager(BaseManager):
    def __init__(self):
        super().__init__()

    def manage(self):
        for obj in self.managed_objects:
            obj.render()

class PointsManager(BaseManager):
    def __init__(self, game_save, player_one, player_two):
        super().__init__()
        self.game_save = game_save
        self.player_one = player_one
        self.player_two = player_two

    def add_points_to_player(self, player):
        player.points += 1
        self.game_save.players_data[player.name] = player.points