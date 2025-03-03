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
    Manages client-side networking for the Pong game.
    Handles registration with the server, processing incoming packets,
    and sending local player position updates.
    """
    def __init__(self, tick_manager, render_manager):
        # Initialize UDP socket in non-blocking mode.
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_address = ('localhost', 12345)
        self.client_id = -1
        self.client_socket.setblocking(False)
        self.socket_list = [self.client_socket]
        
        # Mapping of client IDs to player objects.
        self.clients = {}
        self.counter_threshold = 50  # For potential packet counter validation.
        
        # References to game managers.
        self.tick_manager = tick_manager
        self.render_manager = render_manager
        
        # Position update configuration.
        self.send_position = True
        # 0: do not send, 1: every frame, 2: every other frame, etc.
        self.position_update = 2
        self.position_counter = 0
        
        # Ball instance (spawned on receiving ball update).
        self.ball = None

    def receive_data(self, read_sockets):
        """
        Processes incoming data on the client socket.
        Delegates handling based on the packet type.
        """
        for read_socket in read_sockets:
            if read_socket == self.client_socket:
                try:
                    data, _ = self.client_socket.recvfrom(1024)
                    # Determine the packet type (first byte).
                    packet_type = struct.unpack(">B", data[:1])[0]
                    
                    if packet_type == PacketType.REQUEST_ID:
                        # Handle registration response from the server.
                        _, received_client_id = struct.unpack(">BB", data)
                        self.client_id = received_client_id
                        # Create the local player based on client ID.
                        if self.client_id == 0:
                            self.clients[self.client_id] = player.LeftPlayer(
                                10, 40, pyxel.KEY_W, pyxel.KEY_S, "Player One", True)
                        else:
                            self.clients[self.client_id] = player.RightPlayer(
                                140, 40, pyxel.KEY_W, pyxel.KEY_S, "Player One", False)
                        # Register the player with both tick and render managers.
                        self.clients[self.client_id].register_to_managers(
                            [self.tick_manager, self.render_manager])
                    
                    elif packet_type == PacketType.POSITION:
                        # Unpack POSITION packet. Expected format: >BBBBBIII
                        (packet_type, object_type, client_id, packet_counter,
                         packet_length, x_pos, y_pos, crc) = struct.unpack(">BBBBBIII", data)
                        
                        # Verify packet length and integrity.
                        if packet_length == len(data):
                            data_packed = struct.pack(">BBBBBII", packet_type, object_type,
                                                      client_id, packet_counter, packet_length,
                                                      x_pos, y_pos)
                            computed_crc = zlib.crc32(data_packed)
                            if crc == computed_crc:
                                if object_type == ObjectType.PLAYER:
                                    # Update or spawn a player.
                                    if client_id not in self.clients:
                                        # Create a new player based on local client ID.
                                        if self.client_id == 0:
                                            self.clients[client_id] = player.LeftPlayer(
                                                10, 40, "", "", "Player Two", False)
                                        else:
                                            self.clients[client_id] = player.RightPlayer(
                                                140, 40, "", "", "Player Two", True)
                                        self.clients[client_id].register_to_managers([self.render_manager])
                                        self.clients[client_id].position_packet_counter = packet_counter
                                    # Update player position.
                                    self.clients[client_id].x = x_pos
                                    self.clients[client_id].y = y_pos
                                    self.clients[client_id].position_packet_counter = packet_counter
                                
                                elif object_type == ObjectType.BALL:
                                    # Spawn or update the ball.
                                    if self.ball is None:
                                        self.ball = ball.BallBase(x_pos, y_pos, 4)
                                        self.render_manager.register_object(self.ball)
                                    else:
                                        self.ball.x = x_pos
                                        self.ball.y = y_pos
                                        
                    elif packet_type == PacketType.SPAWN:
                        # Placeholder for SPAWN packet handling.
                        pass
                except Exception:
                    # Ignore exceptions to allow non-blocking operations.
                    pass

    def run_client(self):
        """
        Executes one iteration of client processing.
        Called every frame from the main game loop.
        """
        # Poll the socket for incoming data.
        read_sockets, _, _ = select.select(self.socket_list, [], [], 0)
        self.receive_data(read_sockets)
        
        if self.client_id != -1:
            # Send position updates if registered.
            pos_x = self.clients[self.client_id].x
            pos_y = self.clients[self.client_id].y
            self.position_counter += 1
            if self.position_counter >= self.position_update and self.position_update > 0:
                self.send_position_data(pos_x, pos_y)
                self.position_counter = 0
        else:
            # If not registered, send a REQUEST_ID packet.
            data = struct.pack(">BBII", PacketType.REQUEST_ID, ObjectType.PLAYER, 0, 0)
            self.client_socket.sendto(data, self.server_address)

    def create_packet(self, packet_type, data):
        """
        Constructs a packet with header, payload, and CRC32 checksum.
        
        Header format:
          - Packet type (1 byte)
          - Object type (1 byte; assumed to be PLAYER)
          - Client ID (1 byte)
          - Packet counter (1 byte)
          - Packet length (1 byte)
        
        :param packet_type: Type of the packet (e.g., PacketType.POSITION)
        :param data: Payload data to include in the packet.
        :return: The complete packet as bytes.
        """
        crc_length = 4
        header_length = 5
        packet_length = header_length + len(data) + crc_length
        
        # Construct header and append payload.
        data_packet = struct.pack(
            ">BBBBB",
            packet_type,
            ObjectType.PLAYER,
            self.client_id,
            self.clients[self.client_id].position_packet_counter,
            packet_length
        ) + data
        
        # Update and wrap the packet counter.
        self.clients[self.client_id].position_packet_counter = (
            (self.clients[self.client_id].position_packet_counter + 1) % 256
        )
        
        crc = zlib.crc32(data_packet)
        return data_packet + struct.pack(">I", crc)

    def send_position_data(self, x_pos, y_pos):
        """
        Sends the current player position to the server.
        
        :param x_pos: The player's x-coordinate.
        :param y_pos: The player's y-coordinate.
        """
        data = struct.pack(">II", x_pos, y_pos)
        packet = self.create_packet(PacketType.POSITION, data)
        self.client_socket.sendto(packet, self.server_address)

    def send_request_ID(self):
        """
        Stub for sending a specialized REQUEST_ID packet.
        Currently not implemented.
        """
        pass

# The PongClient instance is created and used by the main game (GameApp) in pong.py.
