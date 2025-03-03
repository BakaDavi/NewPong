import pyxel
import player
import ball
from game_save import GameSave
from managers import PointsManager, PhysicsManager, TickManager, RenderManager
from enums import MyEnum
import pong_client

class GameApp:
    def __init__(self, game_width, game_heigth): 
        
        self.tick_manager = TickManager()
        self.render_manager = RenderManager()
        self.client = pong_client.PongClient(self.tick_manager,self.render_manager)


        #Create client

        #self.ball = ball.BallBase(80, 60, 4, 1, 1, self.points_manager)

        #self.player1.register_to_managers([self.tick_manager, self.render_manager, self.physics_manager])
        #self.player2.register_to_managers([self.tick_manager, self.render_manager, self.physics_manager])
        #self.ball.register_to_managers([self.tick_manager, self.render_manager, self.physics_manager])

        pyxel.init(game_width, game_heigth)
        pyxel.run(self.tick, self.render)

    def tick(self):
        self.tick_manager.manage()
        self.client.run_client()
        #run client
        #self.physics_manager.manage()
        # if pyxel.btnp(pyxel.KEY_F):
        #     self.save()
        # if pyxel.btnp(pyxel.KEY_R):
        #     self.reset()
        if pyxel.btnp(pyxel.KEY_Q):           
           pyxel.quit()
        
    def render(self):
        pyxel.cls(0)
        self.render_manager.manage()
        #pyxel.rect(10,10,20,20,11)

    def save(self):
        if self.player1.name not in self.game_save.players_data:
            self.game_save.players_data[self.player1.name] = 0
        if self.player2.name not in self.game_save.players_data:
            self.game_save.players_data[self.player2.name] = 0
        self.game_save.save_data()

    def reset(self):
        self.player1.reset()
        self.player2.reset()
        self.ball.reset()
        self.game_save.reset()
        


    def load_data(self):
        self.game_save.load_data()
        if not self.game_save.is_new_game:
            names = list(self.game_save.players_data.keys())
            points = list(self.game_save.players_data.values())
            self.player1.name = names[0]
            self.player2.name = names[1]
            self.player1.points = points[0]
            self.player2.points = points[1]
        else:
            self.game_save.players_data = {}


    #pyxel.run(update,draw)
if __name__ == "__main__":
    #create GameSave object
        
    GameApp(160,120)