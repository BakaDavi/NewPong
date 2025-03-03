import os
from enum import Enum, IntEnum

SAVE_FILENAME = os.path.join(os.path.dirname(os.path.abspath(__file__)),"SaveData","save_file.txt")
#player_one:0
#player_two:0

# class CollisionType(Enum):
#     PLAYER = 1
#     HORIZONTAL_BORDER = 2
#     VERTICAL_BORDER = 3

class PacketType(IntEnum):
    REQUEST_ID = 1
    SPAWN = 2
    POSITION = 3
    POINT = 5

class ObjectType(IntEnum):
    NONE = 1
    PLAYER = 2
    BALL = 3

if __name__ == "__main__":
    print(SAVE_FILENAME)