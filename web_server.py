from flask import Flask, render_template, request
from flask_socketio import SocketIO
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app) # socketu folosit pt comunicarea in timp real cu clientul

# Constante si variabile pt joc
WIDTH, HEIGHT = 800, 600
PADDLE_WIDTH, PADDLE_HEIGHT = 10, 100
BALL_SIZE = 20
PADDLE_SPEED = 23
BALL_SPEED_X = 9
BALL_SPEED_Y = 9


left_paddle_y = HEIGHT // 2 - PADDLE_HEIGHT // 2
right_paddle_y = HEIGHT // 2 - PADDLE_HEIGHT // 2
ball_x = WIDTH // 2 - BALL_SIZE // 2
ball_y = HEIGHT // 2 - BALL_SIZE // 2
ball_speed_x = BALL_SPEED_X
ball_speed_y = BALL_SPEED_Y


players = {}
left_paddle_client = None
right_paddle_client = None


left_player_score = 0
right_player_score = 0


def reset_ball(scored_by): # reseteaza mingea la mijloc si schimba directia
    global ball_x, ball_y, ball_speed_x, ball_speed_y, left_player_score, right_player_score
    ball_x = WIDTH // 2 - BALL_SIZE // 2
    ball_y = HEIGHT // 2 - BALL_SIZE // 2
    ball_speed_x *= -1
    ball_speed_y = BALL_SPEED_Y * (1 if ball_speed_y > 0 else -1)

    if scored_by == "left":
        left_player_score += 1
    elif scored_by == "right":
        right_player_score += 1


def update_ball(): # ciclu infinit care muta mingea in functie de viteza si verifica coliziunile
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

        game_state = {
            "left_paddle_y": left_paddle_y,
            "ball_x": ball_x,
            "ball_y": ball_y,
            "right_paddle_y": right_paddle_y,
            "left_player_score": left_player_score,
            "right_player_score": right_player_score
        }
        socketio.emit('update', game_state) # trimite starea jocului la client in timp real

        time.sleep(0.016) # latency de 16ms


@app.route('/')
def index(): # afiseaza pagina html
    return render_template('index.html')


@socketio.on('connect')
def handle_connect(): # se executa la fiecare conectare a unui client si ii atribuie unui client unul din cele doua paddle-uri
    global left_paddle_client, right_paddle_client
    if left_paddle_client is None:
        left_paddle_client = request.sid
    elif right_paddle_client is None:
        right_paddle_client = request.sid


@socketio.on('disconnect')
def handle_disconnect(): # elibereaza paddle-ul unui client la deconectare
    global left_paddle_client, right_paddle_client
    if request.sid == left_paddle_client:
        left_paddle_client = None
    elif request.sid == right_paddle_client:
        right_paddle_client = None


@socketio.on('move')
def handle_move(data): # muta paddle-ul in functie de input-ul clientului
    global left_paddle_y, right_paddle_y
    if request.sid == left_paddle_client:
        if data == 'up' and left_paddle_y > 0:
            left_paddle_y -= PADDLE_SPEED
        elif data == 'down' and left_paddle_y < HEIGHT - PADDLE_HEIGHT:
            left_paddle_y += PADDLE_SPEED
    elif request.sid == right_paddle_client:
        if data == 'up' and right_paddle_y > 0:
            right_paddle_y -= PADDLE_SPEED
        elif data == 'down' and right_paddle_y < HEIGHT - PADDLE_HEIGHT:
            right_paddle_y += PADDLE_SPEED


if __name__ == '__main__':
    ball_thread = threading.Thread(target=update_ball) # thread pt a rula update-ul mingii in paralel cu serverul
    ball_thread.daemon = True # se opreste la inchiderea serverului
    ball_thread.start()
    socketio.run(app, host='0.0.0.0', port=5000,  allow_unsafe_werkzeug=True) # ruleaza Flask pe adresa 0.0.0.0 si portul 5000
