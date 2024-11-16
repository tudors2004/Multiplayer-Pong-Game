import socket
import time
import threading

# Constants
WIDTH, HEIGHT = 800, 600
PADDLE_WIDTH, PADDLE_HEIGHT = 10, 100
BALL_SIZE = 20
PADDLE_SPEED = 20
BALL_SPEED_X = 10
BALL_SPEED_Y = 10

# Server settings
server_ip = "0.0.0.0"
server_port = 5555

# UDP Socket setup
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((server_ip, server_port))
sock.setblocking(False)  # Set socket to non-blocking mode

# Game state
left_paddle_y = HEIGHT // 2 - PADDLE_HEIGHT // 2
right_paddle_y = HEIGHT // 2 - PADDLE_HEIGHT // 2
ball_x = WIDTH // 2 - BALL_SIZE // 2
ball_y = HEIGHT // 2 - BALL_SIZE // 2
ball_speed_x = BALL_SPEED_X
ball_speed_y = BALL_SPEED_Y

# Players
players = {}
left_paddle_client = None
right_paddle_client = None

# Function to update ball position and handle collisions
# Add these variables to keep track of the scores
left_player_score = 0
right_player_score = 0


# Update the reset_ball function to update the scores
def reset_ball(scored_by):
    global ball_x, ball_y, ball_speed_x, ball_speed_y, left_player_score, right_player_score
    ball_x = WIDTH // 2 - BALL_SIZE // 2
    ball_y = HEIGHT // 2 - BALL_SIZE // 2
    ball_speed_x *= -1  # Start moving toward the other player
    ball_speed_y = BALL_SPEED_Y * (1 if ball_speed_y > 0 else -1)

    if scored_by == "left":
        right_player_score += 1
    elif scored_by == "right":
        left_player_score += 1


# Modify the update_ball function to call reset_ball with the correct player
def update_ball():
    global ball_x, ball_y, ball_speed_x, ball_speed_y

    while True:
        ball_x += ball_speed_x
        ball_y += ball_speed_y

        if ball_y <= 0 or ball_y >= HEIGHT - BALL_SIZE:
            ball_speed_y *= -1

        if ball_x <= PADDLE_WIDTH + 30 and left_paddle_y < ball_y < left_paddle_y + PADDLE_HEIGHT:
            ball_speed_x *= -1
        elif ball_x < 0:
            reset_ball("right")
        if ball_x >= WIDTH - PADDLE_WIDTH - 30 - BALL_SIZE and right_paddle_y < ball_y < right_paddle_y + PADDLE_HEIGHT:
            ball_speed_x *= -1
        elif ball_x > WIDTH:
            reset_ball("left")

        game_state = f"{left_paddle_y},{ball_x},{ball_y},{right_paddle_y},{left_player_score},{right_player_score}"
        for player_addr in players:
            sock.sendto(game_state.encode('utf-8'), player_addr)

        time.sleep(0.016)
# Start the ball update thread
ball_thread = threading.Thread(target=update_ball)
ball_thread.daemon = True
ball_thread.start()

# Main game loop
while True:
    try:
        data, addr = sock.recvfrom(1024)
        message = data.decode('utf-8')

        # Assign players to paddles if new
        if addr not in players:
            if left_paddle_client is None:
                left_paddle_client = addr
                players[addr] = {"paddle_y": left_paddle_y}
            elif right_paddle_client is None:
                right_paddle_client = addr
                players[addr] = {"paddle_y": right_paddle_y}
            else:
                continue  # Allow only two players

        # Update paddle position based on message
        if message == 'up':
            if addr == left_paddle_client and left_paddle_y > 0:
                left_paddle_y -= PADDLE_SPEED
            elif addr == right_paddle_client and right_paddle_y > 0:
                right_paddle_y -= PADDLE_SPEED
        elif message == 'down':
            if addr == left_paddle_client and left_paddle_y < HEIGHT - PADDLE_HEIGHT:
                left_paddle_y += PADDLE_SPEED
            elif addr == right_paddle_client and right_paddle_y < HEIGHT - PADDLE_HEIGHT:
                right_paddle_y += PADDLE_SPEED

    except BlockingIOError:
        pass  # No data received, continue the loop