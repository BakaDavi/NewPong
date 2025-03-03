import socket
import struct
from pong_global import ObjectType, PacketType
import zlib
import pyxel

# pakcettype objecttype  id #


DEBUG_MODE = True
HOST = 'localhost'
PORT = 12345

clients = {} #client addresses and clientID
clients_position = {} #clientID and position
next_client_id = 0
clients_to_start_game = 2

class Ball():
    def __init__(self,x,y, size):
        self.x = x
        self.y = y
        self.size = size
        self.send_position = False
        self.dx = 1
        self.dy = 1
        self.game_height = 120
        self.game_width = 160

    def check_collision(self):
        for client_id, (player_x, player_y) in clients_position.items():
            if player_x - self.size <= self.x <= player_x + 10 and player_y <= self.y <= player_y + 40:
                self.on_collide()
                return True
        return False
    

    def check_bounce(self):
        if self.y <= 0 or self.y >= self.game_height - 1:
            self.on_bounce()
        pass
        

    def check_goal(self):
        if self.x <= 0:
            self.x = 80
            self.y = 40
            self.dx = 1
            
        elif self.x >= self.game_width - 1:
            self.x = 80
            self.y = 40
            self.dx = -1

    def update(self):
        self.y += self.dy
        self.x += self.dx
        pass

    def on_collide(self):
        self.dx *= -1

    def on_bounce(self):
        self.dy *= -1
        
    def on_goal(self):
        pass

#self.ball = ball.BallBase(80, 60, 4, 1, 1, self.points_manager)

def create_packet(packet_type, players_to_spawn_in_pos = []):
    #make a general one that takes data as argument
    if packet_type == PacketType.SPAWN:
        #(B+I*2) * num_player
        if len(players_to_spawn_in_pos) > 0:
            num_player_to_spawn = len(players_to_spawn_in_pos)/3
            struct_string = f">BB{'BII'*num_player_to_spawn}"            
            data = struct.pack(struct_string,PacketType.SPAWN,num_player_to_spawn,*players_to_spawn_in_pos)
    elif packet_type == PacketType.REQUEST_ID:
        pass
    elif packet_type == PacketType.POSITION:
        pass

def unpack_packet(data):
    #make a genral one
    pass

def start_server():
    global clients, next_client_id, clients_to_start_game
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((HOST,PORT))
    if DEBUG_MODE:
        print("Server listening on {0}:{1}".format(HOST,PORT))
    
    is_server_running = True

    ball = Ball(80,60, 4)


    while is_server_running:
            data, client_address = server_socket.recvfrom(1024)
            if DEBUG_MODE:
                print("Received {0} bytes of data.".format(len(data)))
            if client_address not in clients:
                client_id = next_client_id
                next_client_id += 1
                clients[client_address] = client_id
                if DEBUG_MODE:
                    print("Assigned ID {0} at client {1}".format(client_id,client_address))
                packet_id, _, client_x_pos, client_y_pos = struct.unpack(">BBII",data)
                if packet_id == PacketType.REQUEST_ID:
                    server_socket.sendto(struct.pack(">BB",PacketType.REQUEST_ID,client_id),client_address) # packet with packettype + clientid 
                    clients_position[client_id] = (client_x_pos,client_y_pos)
                    if len(clients_position) >= clients_to_start_game:
                        ball.send_position = True
                
            else:
                packet_type = struct.unpack(">B",data[:1])[0]
                if packet_type == PacketType.REQUEST_ID:
                    if DEBUG_MODE:
                        print("Resending client ID {0} to client {1}".format(clients[client_address],client_address))
                    server_socket.sendto(struct.pack(">BB",PacketType.REQUEST_ID,clients[client_address]),client_address) # packet with packettype + clientid 
                    packet_id, _, client_x_pos, client_y_pos = struct.unpack(">BBII",data)
                    clients_position[client_id] = (client_x_pos,client_y_pos)
                    
                elif packet_type == PacketType.POSITION:
                    packet_type,object_type, client_id,packet_counter, packet_length, x_pos, y_pos, crc = struct.unpack(">BBBBBIII",data)
                    if packet_length == len(data):
                        data_packed = struct.pack(">BBBBBII",packet_type,object_type, client_id,packet_counter, packet_length, x_pos, y_pos)
                        computed_crc = zlib.crc32(data_packed)
                        if crc == computed_crc:                            
                            clients_position[client_id] = (x_pos,y_pos)                    
                            if DEBUG_MODE:
                                print("received packet with type {0} from clientID {1} wit pos x:{2} y:{3}".format(packet_type,client_id,x_pos,y_pos))
                            for client in clients:
                                print("Check here what client is: ")
                                print(client)
                                if client != client_address:
                                    server_socket.sendto(data, client)
                    if ball.send_position:
                        #create position packet for ball to send to all clients
                        #add CRC
                        ball.update()
                        ball.check_collision()
                        ball.check_bounce()
                        ball.check_goal()
                        data = struct.pack(">BBBBBII",PacketType.POSITION, ObjectType.BALL, client_id, packet_counter, packet_length, ball.x, ball.y)
                        crc = zlib.crc32(data)
                        for client in clients:
                            if client != client_address:
                                server_socket.sendto(data + struct.pack(">I",crc), client)




if __name__ == "__main__":
    print("Server main starting...")
    start_server()