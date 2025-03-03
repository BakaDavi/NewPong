import socket
import struct
import zlib
import pyxel
from pong_global import ObjectType, PacketType

DEBUG_MODE = True
HOST = 'localhost'
PORT = 12345

# Mapping of client addresses to assigned client IDs.
clients = {}
# Mapping of client IDs to their (x, y) positions.
clients_position = {}
next_client_id = 0
# Number of connected clients required to start sending ball updates.
clients_to_start_game = 2

class Ball:
    """
    Represents the ball in the Pong game.
    Handles movement, collision detection with players' paddles,
    bouncing off walls, and resetting after a goal.
    """
    def __init__(self, x, y, size):
        self.x = x
        self.y = y
        self.size = size
        self.send_position = False  # Flag to indicate when to broadcast ball position.
        self.dx = 1  # Horizontal velocity.
        self.dy = 1  # Vertical velocity.
        self.game_height = 120
        self.game_width = 160

    def check_collision(self):
        """
        Checks for collisions with any player's paddle.
        If a collision is detected, reverses the ball's horizontal direction.
        """
        for client_id, (player_x, player_y) in clients_position.items():
            # Assuming paddle dimensions: width = 10, height = 40.
            if player_x - self.size <= self.x <= player_x + 10 and player_y <= self.y <= player_y + 40:
                self.on_collide()
                return True
        return False

    def check_bounce(self):
        """
        Reverses the ball's vertical direction if it touches the top or bottom boundaries.
        """
        if self.y <= 0 or self.y >= self.game_height - 1:
            self.on_bounce()
        #Todo: add the score and save

    def check_goal(self):
        """
        Checks if the ball has reached a goal area.
        Resets the ball to the center and sets the horizontal direction accordingly.
        """
        if self.x < 10: #player position
            self.x = self.game_width // 2
            self.y = self.game_height // 2
            self.dx = 1
        elif self.x > 150: #player position - width
            self.x = self.game_width // 2
            self.y = self.game_height // 2
            self.dx = -1

    def update(self):
        """
        Updates the ball's position based on its current velocity.
        """
        self.x += self.dx
        self.y += self.dy

    def on_collide(self):
        """
        Called when the ball collides with a paddle.
        Reverses the horizontal velocity.
        """
        self.dx *= -1

    def on_bounce(self):
        """
        Called when the ball bounces off the top or bottom walls.
        Reverses the vertical velocity.
        """
        self.dy *= -1

def create_packet(packet_type, players_to_spawn_in_pos=[]):
    """
    Constructs a packet for the given packet type and associated data.
    
    Currently, only the SPAWN packet is implemented.
    
    :param packet_type: The type of packet to create (e.g., PacketType.SPAWN).
    :param players_to_spawn_in_pos: A list containing spawn data for each player,
                                    grouped as [playerID, x, y, ...].
    :return: The packed binary data for the packet.
    """
    if packet_type == PacketType.SPAWN:
        if players_to_spawn_in_pos:
            num_players = len(players_to_spawn_in_pos) // 3
            # Packet structure: PacketType (B), number of players (B), then for each player: ID (B), x (I), y (I)
            struct_format = f">BB{'BII' * num_players}"
            data = struct.pack(struct_format, PacketType.SPAWN, num_players, *players_to_spawn_in_pos)
            return data
    elif packet_type == PacketType.REQUEST_ID:
        # TODO: Implement packet creation for REQUEST_ID
        pass
    elif packet_type == PacketType.POSITION:
        # TODO: Implement packet creation for POSITION updates
        pass
    return b""

def unpack_packet(data):
    """
    Unpacks a packet received from a client.
    This function serves as a placeholder for a more generalized packet unpacking logic.
    
    :param data: The binary packet data.
    :return: Unpacked values as a tuple.
    """
    # TODO: Implement general packet unpacking logic.
    pass

def start_server():
    """
    Starts the UDP server, accepts client registrations, processes incoming packets,
    updates game state, and broadcasts updates to all clients.
    """
    global clients, next_client_id, clients_to_start_game
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((HOST, PORT))
    if DEBUG_MODE:
        print(f"Server listening on {HOST}:{PORT}")
    
    is_server_running = True
    ball = Ball(80, 60, 4)

    while is_server_running:
        data, client_address = server_socket.recvfrom(1024)
        if DEBUG_MODE:
            print(f"Received {len(data)} bytes from {client_address}")

        # Handle new client registration.
        if client_address not in clients:
            client_id = next_client_id
            next_client_id += 1
            clients[client_address] = client_id
            if DEBUG_MODE:
                print(f"Assigned ID {client_id} to new client {client_address}")

            # Expecting registration packet format: >BBII (PacketType, unused, x_pos, y_pos)
            packet_id, _, client_x_pos, client_y_pos = struct.unpack(">BBII", data)
            if packet_id == PacketType.REQUEST_ID:
                # Send the assigned client ID back to the client.
                response = struct.pack(">BB", PacketType.REQUEST_ID, client_id)
                server_socket.sendto(response, client_address)
                clients_position[client_id] = (client_x_pos, client_y_pos)
                # Start ball updates once enough clients have registered.
                if len(clients_position) >= clients_to_start_game:
                    ball.send_position = True

        else:
            # Retrieve the packet type from the first byte.
            packet_type = struct.unpack(">B", data[:1])[0]
            client_id = clients[client_address]

            if packet_type == PacketType.REQUEST_ID:
                # Client is re-requesting its ID.
                if DEBUG_MODE:
                    print(f"Resending client ID {client_id} to client {client_address}")
                response = struct.pack(">BB", PacketType.REQUEST_ID, client_id)
                server_socket.sendto(response, client_address)
                # Update client's position from the registration packet.
                _, _, client_x_pos, client_y_pos = struct.unpack(">BBII", data)
                clients_position[client_id] = (client_x_pos, client_y_pos)
                
            elif packet_type == PacketType.POSITION:
                # Unpack the POSITION packet. Expected format: >BBBBBIII
                (packet_type, object_type, recv_client_id, packet_counter,
                 packet_length, x_pos, y_pos, crc) = struct.unpack(">BBBBBIII", data)
                if packet_length == len(data):
                    # Verify data integrity using CRC32.
                    data_packed = struct.pack(">BBBBBII", packet_type, object_type,
                                              recv_client_id, packet_counter, packet_length,
                                              x_pos, y_pos)
                    computed_crc = zlib.crc32(data_packed)
                    if crc == computed_crc:
                        # Update the client's position.
                        clients_position[recv_client_id] = (x_pos, y_pos)
                        if DEBUG_MODE:
                            print(f"Received POSITION packet from client {recv_client_id} with position ({x_pos}, {y_pos})")
                        # Broadcast the position update to all other clients.
                        for client in clients:
                            if client != client_address:
                                server_socket.sendto(data, client)
                
                # Update and broadcast the ball's position if the game has started.
                if ball.send_position:
                    ball.update()
                    ball.check_collision()
                    ball.check_bounce()
                    ball.check_goal()
                    # Create a ball position update packet with the same structure as POSITION packets.
                    ball_packet = struct.pack(">BBBBBII", PacketType.POSITION, ObjectType.BALL,
                                              client_id, packet_counter, packet_length,
                                              ball.x, ball.y)
                    crc_ball = zlib.crc32(ball_packet)
                    ball_packet += struct.pack(">I", crc_ball)
                    for client in clients:
                        if client != client_address:
                            server_socket.sendto(ball_packet, client)

if __name__ == "__main__":
    print("Server main starting...")
    start_server()
