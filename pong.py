import pyxel
import player
import ball
from game_save import GameSave
from managers import PointsManager, PhysicsManager, TickManager, RenderManager
from enums import MyEnum
import pong_client

class GameApp:
    def __init__(self, game_width, game_height):
        # Initialize game managers
        self.tick_manager = TickManager()
        self.render_manager = RenderManager()
        
        # Create client for multiplayer functionality
        self.client = pong_client.PongClient(self.tick_manager, self.render_manager)

        # Initialize pyxel game engine with specified dimensions
        pyxel.init(game_width, game_height)
        pyxel.run(self.tick, self.render)

    def tick(self):
        """Update game state each frame"""
        self.tick_manager.manage()
        self.client.run_client()
        
        # Check for quit key press
        if pyxel.btnp(pyxel.KEY_Q):           
           pyxel.quit()
        
    def render(self):
        """Draw game elements to the screen"""
        pyxel.cls(0)  # Clear screen with black background
        self.render_manager.manage()

    def save(self):
        """Save player stats to persistent storage"""
        # Create entries for players if they don't exist
        if self.player1.name not in self.game_save.players_data:
            self.game_save.players_data[self.player1.name] = 0
        if self.player2.name not in self.game_save.players_data:
            self.game_save.players_data[self.player2.name] = 0
        self.game_save.save_data()

    def reset(self):
        """Reset game state to initial conditions"""
        self.player1.reset()
        self.player2.reset()
        self.ball.reset()
        self.game_save.reset()

    def load_data(self):
        """Load previously saved game data"""
        self.game_save.load_data()
        if not self.game_save.is_new_game:
            # Extract player names and scores from saved data
            names = list(self.game_save.players_data.keys())
            points = list(self.game_save.players_data.values())
            self.player1.name = names[0]
            self.player2.name = names[1]
            self.player1.points = points[0]
            self.player2.points = points[1]
        else:
            self.game_save.players_data = {}

if __name__ == "__main__":
    # Create game instance with 160x120 resolution
    GameApp(160, 120)