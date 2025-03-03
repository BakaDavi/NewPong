import struct
import socket
import select
import zlib
from pong_global import PacketType, ObjectType
import player
import ball
import pyxel

class PongClient:
    """
    Manages the client-side networking for the Pong game.
    Responsible for communicating with the server, handling incoming packets,
    and sending local position updates.
    """
    def __init__(self, tick_manager, render_manager):
        # Initialize the UDP socket and set it to non-blocking mode.
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_address = ('localhost', 12345)
        self.client_id = -1       
        self.client_socket.setblocking(False)
        self.socket_list = [self.client_socket]
        
        # Dictionary to map client IDs to their associated player objects.
        self.clients = {}
        
        # Threshold for packet counter differences (if needed for validation).
        self.counter_threshold = 50
        
        # Manager instances for updating and rendering game objects.
        self.tick_manager = tick_manager
        self.render_manager = render_manager
        
        # Control flags for sending updates.
        self.send_position = True
        # 0: do not send; 1: send every frame; 2: every other frame; etc.
        self.position_update = 2
        self.position_counter = 0
        
        # The ball instance (spawned on first ball POSITION packet).
        self.ball = None

    def receive_data(self, read_sockets):
        """
        Processes incoming packets from the server.
        Unpacks the packet type and delegates to the appropriate handler.
        """
        for read_socket in read_sockets:
            if read_socket == self.client_socket:
                try:
                    data, _ = self.client_socket.recvfrom(1024)
                    # Unpack the packet type (first byte)
                    packet_type = struct.unpack(">B", data[:1])[0]
                    
                    if packet_type == PacketType.REQUEST_ID:
                        # Handle server response with client ID assignment.
                        _, received_client_id = struct.unpack(">BB", data)
                        self.client_id = received_client_id
                        if self.client_id == 0:
                            # For client ID 0, create a left player.
                            self.clients[self.client_id] = player.LeftPlayer(
                                10, 40, pyxel.KEY_W, pyxel.KEY_S, "Player One", True)
                        else:
                            # For other clients, create a right player.
                            self.clients[self.client_id] = player.RightPlayer(
                                140, 40, pyxel.KEY_W, pyxel.KEY_S, "Player One", False)
                        # Register the new player to both tick and render managers.
                        self.clients[self.client_id].register_to_managers(
                            [self.tick_manager, self.render_manager])

                    elif packet_type == PacketType.POSITION:  
                        # Unpack the POSITION packet.
                        # Expected format: >BBBBBIII
                        (packet_type, object_type, client_id, packet_counter,
                         packet_length, x_pos, y_pos, crc) = struct.unpack(">BBBBBIII", data)
                         
                        # Validate the packet length and integrity using CRC32.
                        if packet_length == len(data):
                            data_packed = struct.pack(">BBBBBII", packet_type, object_type,
                                                      client_id, packet_counter, packet_length,
                                                      x_pos, y_pos)
                            computed_crc = zlib.crc32(data_packed)
                            if crc == computed_crc:
                                if object_type == ObjectType.PLAYER:
                                    # Handle updates for player objects.
                                    if client_id not in self.clients:
                                        # If the player is not spawned yet, create and register it.
                                        if self.client_id == 0:
                                            self.clients[client_id] = player.LeftPlayer(
                                                10, 40, "", "", "Player Two", False)
                                        else:
                                            self.clients[client_id] = player.RightPlayer(
                                                140, 40, "", "", "Player Two", True)
                                        self.clients[client_id].register_to_managers(
                                            [self.render_manager])
                                        self.clients[client_id].position_packet_counter = packet_counter

                                    # Update player position and packet counter.
                                    self.clients[client_id].x = x_pos
                                    self.clients[client_id].y = y_pos
                                    self.clients[client_id].position_packet_counter = packet_counter

                                elif object_type == ObjectType.BALL:
                                    # Handle ball position updates.
                                    if self.ball is None:
                                        # Create the ball instance and register it with the render manager.
                                        self.ball = ball.BallBase(x_pos, y_pos, 4)
                                        self.render_manager.register_object(self.ball)
                                    else:
                                        # Update ball position.
                                        self.ball.x = x_pos
                                        self.ball.y = y_pos

                    elif packet_type == PacketType.SPAWN:
                        # TODO: Implement SPAWN packet handling when needed.
                        pass
                except Exception:
                    # Ignore exceptions to allow non-blocking operation.
                    pass

    def run_client(self):
        """
        Runs a single iteration of client processing.
        This function is intended to be called within the main game loop.
        """
        # Check for available data without blocking.
        read_sockets, _, _ = select.select(self.socket_list, [], [], 0)
        self.receive_data(read_sockets)
        
        if self.client_id != -1:
            # If the client has been assigned an ID, send position updates.
            pos_x_to_send = self.clients[self.client_id].x
            pos_y_to_send = self.clients[self.client_id].y
            self.position_counter += 1
            
            # Send position data based on the configured update interval.
            if self.position_counter >= self.position_update and self.position_update > 0:
                self.send_position_data(pos_x_to_send, pos_y_to_send)
                self.position_counter = 0
        else:
            # If no client ID yet, send a REQUEST_ID packet to the server.
            data = struct.pack(">BBII", PacketType.REQUEST_ID, ObjectType.PLAYER, 0, 0)
            self.client_socket.sendto(data, self.server_address)

    def create_packet(self, packet_type, data):
        """
        Constructs a packet with a header, the provided data payload, and a CRC32 checksum.
        Header format:
          - Packet type (1 byte)
          - Object type (1 byte, assumed PLAYER)
          - Client ID (1 byte)
          - Packet counter (1 byte)
          - Packet length (1 byte)
        
        :param packet_type: The type of packet to be created.
        :param data: The payload data to be appended to the header.
        :return: A bytes object representing the complete packet.
        """
        crc_length = 4
        header_length = 5
        packet_length = header_length + len(data) + crc_length
        # Construct the header and append the payload.
        data_packet = struct.pack(">BBBBB", packet_type, ObjectType.PLAYER, self.client_id,
                                  self.clients[self.client_id].position_packet_counter, packet_length) + data
        
        # Increment and wrap the position packet counter.
        self.clients[self.client_id].position_packet_counter = (
            (self.clients[self.client_id].position_packet_counter + 1) % 256
        )
        crc = zlib.crc32(data_packet)
        out_packet = data_packet + struct.pack(">I", crc)
        return out_packet

    def send_position_data(self, x_pos, y_pos):
        """
        Packs and sends the current position data to the server.
        """
        data = struct.pack(">II", x_pos, y_pos)
        packet = self.create_packet(PacketType.POSITION, data)
        self.client_socket.sendto(packet, self.server_address)

    def send_request_ID(self):
        """
        Stub for sending a REQUEST_ID packet.
        This could be expanded to use create_packet for consistent packet formatting.
        """
        # TODO: Implement this function if a specialized REQUEST_ID packet is needed.
        pass

# Example usage (typically integrated into the main game loop):
# if __name__ == "__main__":
#     client = PongClient(tick_manager, render_manager)
#     while True:
#         client.run_client()
