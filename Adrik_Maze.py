from graphics import Canvas
from ai import call_gpt
import random
import time
import string

# Constants
CANVAS_WIDTH = 600
CANVAS_HEIGHT = 700  # taller for info panel
GRID_SIZE = 4
CELL_SIZE = CANVAS_WIDTH // GRID_SIZE
INFO_PANEL_HEIGHT = CANVAS_HEIGHT - CANVAS_WIDTH  # 100px info panel at bottom

PLAYER_IMAGES = ["Mario.png", "P1.png", "P2.png", "P3.png", "P4.png", "P5.png", "P6.png"]
GREAT_IMAGES = [f"G{i}.png" for i in range(1, 17)]  # G1.png to G16.png
MAX_SCORE = GRID_SIZE * GRID_SIZE * 10


def load_questions_from_file(filename="questions.txt"):
    questions = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line == "" or "|" not in line:
                continue
            question, answer = line.split("|", 1)
            questions.append((question.strip(), answer.strip()))
    random.shuffle(questions)
    return questions

def get_cell_center(row, col):
    return col * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2

def wrap_text(text, max_chars=30):
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line + " " + word) <= max_chars:
            current_line += " " + word if current_line else word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines[:4]

def draw_maze(canvas):
    tiles = []
    for row in range(GRID_SIZE):
        tile_row = []
        for col in range(GRID_SIZE):
            x0 = col * CELL_SIZE
            y0 = row * CELL_SIZE
            x1 = x0 + CELL_SIZE
            y1 = y0 + CELL_SIZE
            tile = canvas.create_rectangle(x0, y0, x1, y1, color="white", outline="gray")
            tile_row.append(tile)
        tiles.append(tile_row)
    return tiles

def draw_player(canvas, row, col, image_file):
    cx, cy = get_cell_center(row, col)
    size = CELL_SIZE // 2
    return canvas.create_image_with_size(cx - size // 2, cy - size // 2, size, size, image_file)

def show_question_and_input(canvas, question, current_answer):
    canvas.create_rectangle(0, CANVAS_WIDTH, CANVAS_WIDTH, CANVAS_HEIGHT, color="lightyellow")
    cx = 20
    base_y = CANVAS_WIDTH + 10
    wrapped_lines = wrap_text(question, max_chars=60)
    for i, line in enumerate(wrapped_lines):
        canvas.create_text(cx, base_y + i * 25, text=line, font_size=18, color="black", anchor="nw")
    canvas.create_text(cx, base_y + len(wrapped_lines) * 25 + 15,
                       text=f"Your answer: {current_answer}", font_size=20, color="blue", anchor="nw")

def show_score_round(canvas, score, round_num):
    width = 130
    height = 80
    x = CANVAS_WIDTH - 20
    y = CANVAS_WIDTH + 20
    canvas.create_rectangle(x - width, y - 20, x, y + height, color="lightblue", outline="black")
    canvas.create_text(x - width + 10, y, text=f"Score: {score}", font_size=16, color="darkgreen", anchor="nw")
    canvas.create_text(x - width + 10, y + 30, text=f"Round: {round_num}", font_size=16, color="darkgreen", anchor="nw")

def quiz(canvas, row, col, score, round_num, cx, cy, question_text, correct_answer):
    answer = ""
    show_question_and_input(canvas, question_text, answer)
    show_score_round(canvas, score[0], round_num)
    feedback_ids = []

    while True:
        keys = canvas.get_new_key_presses()
        for key in keys:
            if key == "Enter":
                user_ans = answer.strip().lower().rstrip(string.punctuation)
                correct_ans = correct_answer.strip().lower().rstrip(string.punctuation)
                for fid in feedback_ids:
                    canvas.delete(fid)
                feedback_ids.clear()
                if user_ans == correct_ans:
                    score[0] += 10
                    image_file = random.choice(GREAT_IMAGES)
                    feedback_ids.append(canvas.create_image_with_size(
                        cx - CELL_SIZE // 4, cy - CELL_SIZE // 4,
                        CELL_SIZE // 2, CELL_SIZE // 2, image_file
                    ))
                    feedback_ids.append(canvas.create_text(
                         cx + 1, cy + 21,
                        text="-10 points!", font_size=12, color="green"
                    ))
                    show_score_round(canvas, score[0], round_num)
                    time.sleep(1)
                    return True, question_text, correct_answer, True, feedback_ids
                else:
                    score[0] -= 10
                    feedback_ids.append(canvas.create_text(
                        cx-30, cy+20,
                        text=f"❌ Answer: {correct_answer}",
                        font_size=12, color="red"
                    ))
                    feedback_ids.append(canvas.create_text(
                         cx-1, cy,
                        text="-10 points!", font_size=12, color="red"
                    ))
                    show_score_round(canvas, score[0], round_num)
                    time.sleep(1)
                    return True, question_text, correct_answer, False, feedback_ids
            elif key == "Backspace":
                answer = answer[:-1]
                show_question_and_input(canvas, question_text, answer)
                show_score_round(canvas, score[0], round_num)
            elif len(key) == 1:
                answer += key
                show_question_and_input(canvas, question_text, answer)
                show_score_round(canvas, score[0], round_num)
        time.sleep(0.05)

def main():
    while True:
        canvas = Canvas(CANVAS_WIDTH, CANVAS_HEIGHT)
         # Intro screen with background image and click prompt
        canvas.create_rectangle(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT, color="yellow")
        canvas.create_image_with_size(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT, "Adrik.png")
        canvas.create_text(CANVAS_WIDTH // 2, CANVAS_HEIGHT - 40,
                        text="Click anywhere to begin!", font_size=28, color="blue")
        canvas.wait_for_click()
        canvas.clear()
        tiles = draw_maze(canvas)
        player_row, player_col = 0, 0
        avatar = random.choice(PLAYER_IMAGES)
        player = draw_player(canvas, player_row, player_col, avatar)
        score = [0]
        round_num = 1
        feedback_map = {}
        question_pool = load_questions_from_file("questions.txt")


        answered_cells = set()
        total_cells = GRID_SIZE * GRID_SIZE

        # Show first quiz immediately
        cx, cy = get_cell_center(player_row, player_col)
        question_text, correct_answer = question_pool.pop()
        cleared, q_text, ans, correct, new_feedback = quiz(canvas, player_row, player_col, score, round_num, cx, cy, question_text, correct_answer)
        round_num += 1
        feedback_map[(player_row, player_col)] = new_feedback
        answered_cells.add((player_row, player_col))

        while True:
            # If all answered, show end screen and restart game
            if len(answered_cells) == total_cells:
                cx, cy = get_cell_center(player_row, player_col)
                canvas.create_image_with_size(cx - CELL_SIZE // 2, cy - CELL_SIZE // 2, CELL_SIZE, CELL_SIZE, "Game_over.png")
                canvas.create_text(cx, cy + CELL_SIZE // 1.5,
                                   text=f"🎉 You Won! {score[0]}/{MAX_SCORE}",
                                   font_size=18, color="green")
                time.sleep(4)
                canvas.clear()
                break  # restart game loop

            # Auto-move to next unanswered cell row-wise
            next_cell_found = False
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE):
                    if (r,c) not in answered_cells:
                        player_row, player_col = r, c
                        next_cell_found = True
                        break
                if next_cell_found:
                    break

            cx, cy = get_cell_center(player_row, player_col)
            canvas.moveto(player, cx - CELL_SIZE // 4, cy - CELL_SIZE // 4)

            # Clear old feedback for this cell
            if (player_row, player_col) in feedback_map:
                for item in feedback_map[(player_row, player_col)]:
                    canvas.delete(item)
                feedback_map[(player_row, player_col)] = []

            # Pop next question if pool empty reload
            if not question_pool:
                question_pool = preload_questions(GRID_SIZE * GRID_SIZE)
            
            question_text, correct_answer = question_pool.pop()
            cleared, q_text, ans, correct, new_feedback = quiz(canvas, player_row, player_col, score, round_num, cx, cy, question_text, correct_answer)
            round_num += 1
            feedback_map[(player_row, player_col)] = new_feedback
            answered_cells.add((player_row, player_col))

if __name__ == "__main__":
    main()
