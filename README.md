Pong Multiplayer Network Game Documentation
===========================================

This documentation details a networked implementation of the classic Pong game using Python and the Pyxel library. The game leverages a client-server architecture, UDP communication, and a custom binary packet protocol to synchronize game state across multiple players. It covers the project overview, code structure, networking protocol, core game components, manager systems, and known limitations.

* * * * *

Table of Contents
-----------------

1.  [Overview](#overview)
2.  [Project Architecture](#project-architecture)
3.  [Code Structure](#code-structure)
4.  [Networking Protocol](#networking-protocol)
5.  [Server Design](#server-design)
6.  [Client Design](#client-design)
7.  [Manager System](#manager-system)
8.  [Game Flow](#game-flow)
9.  [Implementation Notes](#implementation-notes)
10. [Known Issues and Limitations](#known-issues-and-limitations)

* * * * *

Overview
--------

The Pong Multiplayer Network Game is a modern take on the classic Pong game. It implements a client-server model where the server is responsible for authoritative game state management (including game physics and client synchronization), while clients handle user input and rendering using the Pyxel library. Communication occurs over UDP using a custom binary protocol that ensures data integrity via CRC32 checksums.

* * * * *

Project Architecture
--------------------

The game is built on a clear separation of concerns:

-   **Server Responsibilities:**
    -   Accepts and manages client connections.
    -   Maintains and updates the overall game state (player positions, ball physics, scores).
    -   Processes incoming packets (e.g., registration, position updates) and broadcasts game state changes.
-   **Client Responsibilities:**
    -   Connects to the server and receives a unique player ID.
    -   Sends local player input and position updates to the server.
    -   Receives and processes state updates to render the game locally.

Both components work together to provide a smooth multiplayer experience.

* * * * *

Code Structure
--------------

The project is organized into several modules:

### Core Files

-   **`pong.py`**\
    The main game entry point. Initializes game components and runs the game loop by integrating tick (game logic) and render managers.

-   **`pong_global.py`**\
    Defines global constants, enumerations, and packet types used across the project (e.g., `PacketType` and `ObjectType`).

-   **`enums.py`**\
    Contains additional enumerations to support game logic.

-   **`player.py`**\
    Implements player paddle classes. Differentiates between left and right players, manages movement, and handles network synchronization via packet counters.

-   **`ball.py`**\
    Implements the ball class. Although some physics logic is now handled by the server, this module still defines ball rendering and object registration.

-   **`managers.py`**\
    Contains manager classes (e.g., `TickManager`, `RenderManager`, `PhysicsManager`, and `PointsManager`) that update game objects, handle physics/collision detection, and render game elements.

-   **`game_save.py`**\
    Handles game state persistence including loading and saving player scores.

### Networking Files

-   **`pong_client.py`**\
    Manages client-side networking: establishing connections, sending local input updates, and processing state updates from the server.

-   **`pong_server.py`**\
    Implements server functionality: accepting clients, running the physics simulation, processing packets, and broadcasting updated game state.

*This structure reflects a transition from a standalone Pong game to a fully networked multiplayer experience.*

* * * * *

Networking Protocol
-------------------

The game employs a custom UDP binary protocol for communication between clients and the server. Key details include:

### Packet Types

| Packet Type | ID | Purpose |
| --- | --- | --- |
| REQUEST_ID | 1 | Client registration and ID assignment |
| SPAWN | 2 | Notifying clients of new game objects |
| POSITION | 3 | Updating positions of players/ball |
| POINT | 5 | Updating scores when a point is scored |

Each packet contains specific fields and includes a CRC32 checksum to validate integrity.

### Example Packet Structures

#### REQUEST_ID Packet

| Field | Type | Size (bytes) | Description |
| --- | --- | --- | --- |
| Packet Type | byte | 1 | Set to `PacketType.REQUEST_ID` |
| Object Type | byte | 1 | Indicates player type |
| X Position | uint32 | 4 | Initial X coordinate |
| Y Position | uint32 | 4 | Initial Y coordinate |

#### POSITION Packet

| Field | Type | Size (bytes) | Description |
| --- | --- | --- | --- |
| Packet Type | byte | 1 | Set to `PacketType.POSITION` |
| Object Type | byte | 1 | PLAYER or BALL indicator |
| Client ID | byte | 1 | Sender's unique ID |
| Packet Counter | byte | 1 | Sequence number for ordering |
| Packet Length | byte | 1 | Total length of the packet |
| X Position | uint32 | 4 | Current X coordinate |
| Y Position | uint32 | 4 | Current Y coordinate |
| CRC | uint32 | 4 | CRC32 checksum for data validation |

*Details consolidated from both documentation sources .*

* * * * *

Server Design
-------------

The server forms the backbone of the multiplayer experience:

-   **Client Management:**\
    The server maintains a dictionary of connected clients and their positions, assigning each a unique ID upon registration.

-   **Ball Physics:**\
    A dedicated `Ball` class manages ball movement, collision detection (with players and walls), and resetting after a goal.

-   **Packet Handling:**\
    The server receives and processes various packets (e.g., registration, position updates) and uses them to update the game state before broadcasting the changes.

-   **Flow:**

    1.  Initialize the server socket and bind to a port.
    2.  Accept client connections and assign unique IDs.
    3.  Process incoming packets to update game state.
    4.  Run the physics simulation (updating ball and player positions).
    5.  Broadcast updated positions and events to all connected clients.

* * * * *

Client Design
-------------

The client is responsible for handling user interactions and rendering:

-   **Network Management:**

    -   Connects to the server and sends a `REQUEST_ID` packet.
    -   Continuously sends position updates based on local input.
    -   Processes incoming packets to update local representations of players and the ball.
-   **Game Objects:**

    -   Manages both local and remote player objects.
    -   Renders the game ball and players based on received game state.
-   **Flow:**

    1.  Connect to the server and request a player ID.
    2.  Initialize local player based on the received ID.
    3.  Capture local player input and send periodic position updates.
    4.  Update game state and render frames based on state data from the server.

*The client logic is integrated into the main game loop, ensuring consistent state updates and rendering.*

* * * * *

Manager System
--------------

The project utilizes a set of managers to organize game logic:

-   **TickManager:**\
    Updates game objects each frame by calling their `tick()` method. This includes processing input and updating object states.

-   **RenderManager:**\
    Handles drawing all registered game objects onto the screen every frame.

-   **PhysicsManager:**\
    Processes collision detection between game objects and manages interactions (such as ball bounces and border collisions).

-   **PointsManager:**\
    Tracks player scores and interfaces with the game save system to persist and update score data.

*Example registration pattern:*

python

CopiaModifica

`def register_to_managers(self, managers):
    for manager in managers:
        manager.register_object(self)`

*This pattern allows dynamic object registration across multiple managers for synchronized updates.*

* * * * *

Game Flow
---------

### Initialization

1.  **Server Startup:**

    -   The server initializes, binds to a network port, and begins listening for client connections.
2.  **Client Connection:**

    -   Clients connect to the server, send a `REQUEST_ID` packet, and receive a unique ID.
    -   The server broadcasts a SPAWN event to inform other clients of the new player.

### Main Game Loop

1.  **Input and Updates:**

    -   Clients capture local input and send position updates to the server.
    -   The server processes these updates, runs the physics simulation (e.g., ball movement, collision handling), and updates the authoritative game state.
2.  **Broadcast and Render:**

    -   The server broadcasts updated positions and scores to all clients.
    -   Clients update their local game state and render the updated frame using the RenderManager.
3.  **Synchronization:**

    -   Sequence numbers and CRC32 checksums ensure that packets are processed in order and without corruption.
    -   Regular updates maintain a smooth and consistent multiplayer experience.

* * * * *

Implementation Notes
--------------------

-   **Transition to Client-Server:**\
    The project initially contained standalone game logic (with direct physics processing) but has evolved into a networked architecture. Many physics functions in `ball.py` have been commented out as the server now handles these operations.

-   **Object Registration:**\
    Game objects are dynamically registered with various managers (Tick, Render, Physics) to simplify update and rendering logic.

-   **Input Handling:**\
    Local player input is processed using Pyxel's input functions. In multiplayer mode, this input is sent to the server rather than being processed entirely on the client side.

-   **Data Persistence:**\
    The game includes a save system (`game_save.py`) for storing player scores, with simple file-based read/write operations.

* * * * *

Known Issues and Limitations
----------------------------

-   **Incomplete Packet Handling:**\
    Some functions related to packet processing and error recovery remain basic, limiting robustness.

-   **Error Recovery:**\
    The system has limited capabilities for recovering from network errors or corrupted packets.

-   **Hardcoded Configurations:**\
    Certain configuration values (such as game update intervals) are hardcoded, reducing flexibility.

-   **Basic Game Features:**\
    The game currently implements only the core Pong mechanics. Future enhancements could include advanced physics, power-ups, or more sophisticated multiplayer features.