from pong_global import SAVE_FILENAME

class GameSave:
    def __init__(self):
        self.saved_data = ""
        self.is_new_game = False
        self.players_data = {}
        try:
            save_handle = open(SAVE_FILENAME,"r")
            self.saved_data = save_handle.readlines()
            save_handle.close()
        except Exception as exception:
            self.is_new_game = True
            if exception.errno == 2:
                print("No save data found. Starting new game.")
            else:
                print("Error reading save data")

    def load_data(self):
        if self.is_new_game == False:
            if len(self.saved_data) < 2:
                print("Missing data in saved data. Launching new game.")
                self.is_new_game = True
                return
            for line in self.saved_data:
                if ":" not in line:
                    print("Error in saved file data. Launching new game.")
                    self.is_new_game = True
                    return
                name = line.split(":")[0]
                points = line.split(":")[1]                
                self.players_data[name] = int(points)

    def save_data(self):
        try:
            with open(SAVE_FILENAME,"w") as save_file:
                for player in self.players_data:
                    save_file.write("{0}:{1}\n".format(player,self.players_data[player]))
        except Exception as e:
            print(e)

    def reset(self):
        self.players_data = {}
        self.is_new_game = True
            