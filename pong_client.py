import struct
import socket
import select
import zlib
from pong_global import PacketType, ObjectType
import player
import ball
import pyxel

#every packet:
#first byte is packet type

#Spawn
#BB (BII)*num_player

#POS
#struct.pack(">BBBIIBI",packet_type,self.client_id,counter,x_pos,y_pos,packet_length,CRC)

class PongClient():
    def __init__(self, tick_manager, render_manager):
        self.client_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.server_address = ('localhost',12345)
        self.client_id = -1       
        self.client_socket.setblocking(False)
        self.socket_list = [self.client_socket]
        self.clients = {} #ClientID, Player
        self.counter_threshold = 50
        self.tick_manager = tick_manager
        self.render_manager = render_manager
        self.send_position = True
        self.position_update = 2 #0 will not send, 1 will send every frame, 2 will send every other frame, 3 will send every third frame and so on
        self.position_counter = 0
        self.ball = ""

    def receive_data(self, read_sockets):
        for read_socket in read_sockets:
            if read_socket == self.client_socket:
                try:
                    data, _ = self.client_socket.recvfrom(1024)
                    packet_type = struct.unpack(">B",data[:1])[0]
                    #All of this can be wrapped in a ManagePacket(PacketType) function with subfunctions
                    if packet_type == PacketType.REQUEST_ID:
                        #should be wrapped in a function
                        packet_type, received_client_id = struct.unpack(">BB",data)                        
                        self.client_id = received_client_id
                        if self.client_id == 0:
                            self.clients[self.client_id] = player.LeftPlayer(10, 40, pyxel.KEY_W, pyxel.KEY_S, "Player One", True)
                            self.clients[self.client_id].register_to_managers([self.tick_manager,self.render_manager])
                        else:
                            self.clients[self.client_id] = player.RightPlayer(140, 40, pyxel.KEY_W, pyxel.KEY_S, "Player One", False)
                            self.clients[self.client_id].register_to_managers([self.tick_manager,self.render_manager])

                    elif packet_type == PacketType.POSITION:  
                        #Should be wrapped in a function. 
                        #Ideally a first more general one that unpack the data and then pass on data to subfunctions                      
                        packet_type, object_type, client_id,packet_counter, packet_length, x_pos, y_pos, crc = struct.unpack(">BBBBBIII",data)                        
                        if packet_length == len(data):
                            data_packed = struct.pack(">BBBBBII",packet_type,object_type, client_id,packet_counter, packet_length, x_pos, y_pos)
                            computed_crc = zlib.crc32(data_packed)
                            if crc == computed_crc:
                                if object_type == ObjectType.PLAYER:
                                    if client_id not in self.clients:
                                        #Do Spawn
                                        if self.client_id == 0:
                                            self.clients[client_id] = player.LeftPlayer(10, 40, "", "", "Player Two", False)
                                            self.clients[client_id].register_to_managers([self.render_manager])
                                        else:
                                            self.clients[client_id] = player.RightPlayer(140, 40, "", "", "Player Two", True)
                                            self.clients[client_id].register_to_managers([self.render_manager])
                                        self.clients[client_id].position_packet_counter = packet_counter

                                    #elif packet_counter > self.clients[client_id].position_packet_counter or (packet_counter == 0 and self.clients[client_id].position_packet_counter >= 240) and abs(packet_counter - self.clients[client_id].position_packet_counter) < self.counter_threshold:
                                    self.clients[client_id].x = x_pos
                                    self.clients[client_id].y = y_pos
                                    self.clients[client_id].position_packet_counter = packet_counter
                                elif object_type == ObjectType.BALL:
                                    if not self.ball:
                                        self.ball = ball.BallBase(x_pos,y_pos,4)
                                        self.render_manager.register_object(self.ball)
                                        #spawn ball
                                        #register only to render manager
                                        pass
                                    else:
                                        self.ball.x = x_pos
                                        self.ball.y = y_pos
                                        #set ball position
                                        pass

                    
                    elif packet_type == PacketType.SPAWN:
                        # num_players = struct.unpack(">B",data[1:2])[0]
                        # unpack_string = f">{'BI'*num_players}"
                        # unpacked_data = struct.unpack(unpack_string,data[2:])
                        # for player_to_spawn_index in range(0,len(unpacked_data),3):
                        #     player_id = unpacked_data[player_to_spawn_index]
                        #     player_x_pos = unpacked_data[player_to_spawn_index+1]
                        #     player_y_pos = unpacked_data[player_to_spawn_index+2]
                        #     #use data to spawn player in position
                        #     self.clients[player_id] = (player_x_pos,player_y_pos)
                            #self.clients_pos_counters[player_id] = -1
                        pass
                except:
                    pass

    def run_client(self):   
        #run client is not into a while since it gets incorporated into the game loop
        read_sockets, _ , _ = select.select(self.socket_list,[],[],0)
        self.receive_data(read_sockets)
        if self.client_id != -1:
            pos_x_to_send = self.clients[self.client_id].x
            pos_y_to_send = self.clients[self.client_id].y

            #sending depending on position update
            self.position_counter += 1
            if self.position_counter >= self.position_update and self.position_update > 0:
                self.send_position_data(pos_x_to_send,pos_y_to_send)
                self.position_counter = 0
        else:
            #should use the general createpacket
            data = struct.pack(">BBII",PacketType.REQUEST_ID,ObjectType.PLAYER,0,0)
            self.client_socket.sendto(data,self.server_address)

    def create_packet(self,packet_type,data):
        #creating a packet for position. Ideally this should be generalized in order to be used for every type of packet
        crc_length = 4
        header_length = 5
        packet_length = header_length + len(data) + crc_length#(lenght of data + length of crc)
        data_packet = struct.pack(">BBBBB",packet_type,ObjectType.PLAYER,self.client_id,self.clients[self.client_id].position_packet_counter,packet_length) + data
        self.clients[self.client_id].position_packet_counter += 1
        if self.clients[self.client_id].position_packet_counter > 255:
            self.clients[self.client_id].position_packet_counter = 0        
        crc = zlib.crc32(data_packet)
        out_packet = data_packet + struct.pack(">I",crc)
        
        return out_packet

    def send_position_data(self, x_pos, y_pos):
        data = struct.pack(">II",x_pos,y_pos)
        #send data position using create packet. We should have similar functions for all type of packets
        packet = self.create_packet(PacketType.POSITION,data)
        self.client_socket.sendto(packet,self.server_address)

    def send_request_ID(self):
        #use create packet to generate data
        #send data
        pass



# if __name__ == "__main__":
#     client = PongClient()
#     client.run_client()
