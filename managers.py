import pyxel

class BaseManager:
    """
    Base Manager Class that provides object registration and management interface.
    """
    def __init__(self):
        self.managed_objects = []

    def manage(self):
        """
        Placeholder method to be overridden by subclasses.
        """
        pass

    def register_object(self, obj):
        """
        Registers an object to the manager list.
        """
        self.managed_objects.append(obj)

class PhysicsManager(BaseManager):
    """
    Manages physics calculations like collision detection and boundary checks.
    """
    def __init__(self):
        super().__init__()

    def manage(self):
        """
        Runs border checks and collision detection for all registered objects.
        """
        num_objects = len(self.managed_objects)

        for i in range(num_objects):
            self.check_borders(self.managed_objects[i])
            for j in range(i + 1, num_objects):
                if self.check_collisions(self.managed_objects[i], self.managed_objects[j]):
                    self.managed_objects[i].on_collide(self.managed_objects[j])
                    self.managed_objects[j].on_collide(self.managed_objects[i])

    def check_collisions(self, obj1, obj2):
        """
        Detects Axis-Aligned Bounding Box (AABB) collisions between two objects.
        """
        x_collision = (obj1.x < obj2.x + obj2.width) and (obj1.x + obj1.width > obj2.x)
        y_collision = (obj1.y < obj2.y + obj2.height) and (obj1.y + obj1.height > obj2.y)

        return x_collision and y_collision

    def check_borders(self, obj):
        """
        Detects out-of-bounds collisions with screen borders.
        """
        if obj.y >= pyxel.height - obj.height or obj.y <= 0:
            obj.on_out_of_bounds(True)  # Vertical boundaries
        
        if obj.x >= pyxel.width - obj.width or obj.x <= 0:
            obj.on_out_of_bounds(False)  # Horizontal boundaries

class TickManager(BaseManager):
    """
    Updates registered objects each game frame.
    """
    def __init__(self):
        super().__init__()

    def manage(self):
        """
        Calls the `tick()` method for every registered object.
        """
        for obj in self.managed_objects:
            obj.tick()

class RenderManager(BaseManager):
    """
    Draws registered objects on the screen.
    """
    def __init__(self):
        super().__init__()

    def manage(self):
        """
        Calls the `render()` method for every registered object.
        """
        for obj in self.managed_objects:
            obj.render()

class PointsManager(BaseManager):
    """
    Manages the player scores and interacts with the game save system.
    """
    def __init__(self, game_save, player_one, player_two):
        super().__init__()
        self.game_save = game_save
        self.player_one = player_one
        self.player_two = player_two

    def add_points_to_player(self, player):
        """
        Increments the player's score and updates the save data.
        """
        print(f"Point added to {player.name}")  # Debug print
        player.points += 1
        self.game_save.players_data[player.name] = player.points
