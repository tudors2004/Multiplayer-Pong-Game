import socket
import pygame

# Constants
WIDTH, HEIGHT = 800, 600
PADDLE_WIDTH = 10
PADDLE_HEIGHT = 100
BALL_SIZE = 20
PADDLE_SPEED = 15

# Pygame setup
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong Game")

# UDP Client settings
server_ip = "127.0.0.1"
server_port = 5555
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(1)

# Paddle and ball positions
paddle_y = HEIGHT // 2 - PADDLE_HEIGHT // 2
opponent_paddle_y = paddle_y
ball_x, ball_y = WIDTH // 2, HEIGHT // 2

running = True
# Add these variables to keep track of the scores
left_player_score = 0
right_player_score = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or pygame.key.get_pressed()[pygame.K_ESCAPE]:
            running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        sock.sendto(b'up', (server_ip, server_port))
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        sock.sendto(b'down', (server_ip, server_port))

    try:
        data, _ = sock.recvfrom(1024)
        decoded = data.decode('utf-8')
        paddle_y, ball_x, ball_y, opponent_paddle_y, left_player_score, right_player_score = map(int, decoded.split(','))

    except socket.timeout:
        pass

    screen.fill((0, 0, 0))
    pygame.draw.rect(screen, (255, 255, 255), (30, paddle_y, PADDLE_WIDTH, PADDLE_HEIGHT))
    pygame.draw.rect(screen, (255, 255, 255), (WIDTH - 30 - PADDLE_WIDTH, opponent_paddle_y, PADDLE_WIDTH, PADDLE_HEIGHT))
    pygame.draw.ellipse(screen, (255, 255, 255), (ball_x, ball_y, BALL_SIZE, BALL_SIZE))

    # Display the scores
    font = pygame.font.Font(None, 50)
    score_text = font.render(f"{left_player_score}  {right_player_score}", True, (255, 255, 255))
    text_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT - 50))
    screen.blit(score_text, text_rect)

    pygame.display.flip()
    pygame.time.Clock().tick(120)

pygame.quit()
sock.close()