# ==============================================
#  app.py — PyQuiz: Python Terminal Quiz System
#  Converted from app.js (JavaScript) to Python
#
#  How to run:
#    python app.py
#
#  Make sure questions.json is in the same folder!
# ==============================================

# ── IMPORTS ────────────────────────────────
import json        # to read questions.json (like JSON.parse in JS)
import random      # to shuffle questions (like Math.random in JS)
import os          # to clear the terminal screen
import time        # to run the countdown timer
import threading   # to run the timer in the background
from datetime import datetime  # to record the date of each quiz


# ==============================================
#  QUIZ CLASS
#  In JavaScript we had "const App = { ... }"
#  In Python, we use a class instead.
#  All state variables become self.variable
# ==============================================
class QuizApp:

    # ------------------------------------------
    #  __init__ = constructor
    #  This runs automatically when we create
    #  a QuizApp() object — like JS's init()
    # ------------------------------------------
    def __init__(self):
        # All state variables (same as JS state)
        self.all_questions    = []     # all questions from JSON
        self.active_questions = []     # questions for current quiz
        self.current_index    = 0      # which question we're on
        self.score            = 0.0    # player's score
        self.correct_count    = 0      # how many correct answers
        self.wrong_count      = 0      # how many wrong answers
        self.skipped_count    = 0      # how many skipped (timed out)
        self.penalty_total    = 0.0    # total marks deducted

        self.player_name      = ""     # player's name
        self.selected_diff    = "easy" # chosen difficulty
        self.negative_marking = False  # is negative marking on?

        self.time_left        = 30     # seconds left for question
        self.answered         = False  # did player answer in time?
        self.timer_thread     = None   # background timer thread
        self.timer_expired    = False  # did the timer run out?

        self.score_history    = []     # list of past quiz results
        self.history_file     = "quiz_history.json"  # save file name

        # Load saved history when app starts
        self.load_history()

        # Load questions from JSON file
        self.load_questions()


    # ==========================================
    #  LOAD QUESTIONS
    #  Reads questions.json from disk
    #  Like: fetch('questions.json') in JS
    # ==========================================
    def load_questions(self):
        try:
            # Open the file and parse its JSON content
            with open("questions.json", "r", encoding="utf-8") as f:
                self.all_questions = json.load(f)
            print(f"✅ Loaded {len(self.all_questions)} questions.\n")

        except FileNotFoundError:
            # File not found — show helpful error message
            print("❌ ERROR: questions.json not found!")
            print("   Make sure questions.json is in the same folder as app.py")
            input("   Press Enter to exit...")
            exit()  # stop the program

        except json.JSONDecodeError:
            # File found but JSON is invalid
            print("❌ ERROR: questions.json has invalid format!")
            input("   Press Enter to exit...")
            exit()


    # ==========================================
    #  LOAD HISTORY
    #  Reads saved quiz history from a JSON file
    #  Like: localStorage.getItem() in JS
    # ==========================================
    def load_history(self):
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                self.score_history = json.load(f)
        except FileNotFoundError:
            # No history file yet — that's fine, start with empty list
            self.score_history = []
        except json.JSONDecodeError:
            self.score_history = []


    # ==========================================
    #  SAVE HISTORY
    #  Saves score history to a JSON file
    #  Like: localStorage.setItem() in JS
    # ==========================================
    def save_history(self):
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(self.score_history, f, indent=2)


    # ==========================================
    #  CLEAR SCREEN
    #  Clears the terminal for a clean look
    #  Like: switching screens in JS
    # ==========================================
    def clear_screen(self):
        # 'cls' for Windows, 'clear' for Mac/Linux
        os.system('cls' if os.name == 'nt' else 'clear')


    # ==========================================
    #  PRINT HEADER
    #  Shows the app title at the top
    # ==========================================
    def print_header(self):
        print("=" * 50)
        print("          🐍  PyQUIZ — Python Edition  🐍")
        print("=" * 50)
        print()


    # ==========================================
    #  PRINT DIVIDER
    #  Prints a horizontal line separator
    # ==========================================
    def print_divider(self):
        print("-" * 50)


    # ==========================================
    #  GET VALID INPUT
    #  Keeps asking until user gives valid input
    #  Like: input validation in JS
    #
    #  valid_options = list of allowed choices
    #  e.g., ["1", "2", "3", "4"]
    # ==========================================
    def get_valid_input(self, prompt, valid_options):
        while True:
            # Ask the user
            user_input = input(prompt).strip()

            # Check if input is in allowed options
            if user_input in valid_options:
                return user_input  # valid — return it
            else:
                # Invalid — show error and ask again
                print(f"  ⚠️  Invalid input! Please enter one of: {', '.join(valid_options)}")


    # ==========================================
    #  SHUFFLE LIST
    #  Randomly reorders a list
    #  Like: shuffleArray() in JS
    # ==========================================
    def shuffle_list(self, lst):
        # Make a copy so we don't modify the original
        shuffled = lst.copy()
        random.shuffle(shuffled)  # Python's built-in shuffle
        return shuffled


    # ==========================================
    #  SHOW MAIN MENU
    #  The home screen — like screen-menu in JS
    # ==========================================
    def show_menu(self):
        while True:
            self.clear_screen()
            self.print_header()

            # Show last score if history exists
            if self.score_history:
                last = self.score_history[-1]  # get most recent
                print(f"  📌 Last: {last['name']} scored "
                      f"{last['score']:.2f}/{last['total']} "
                      f"({last['rank']})\n")

            # Print menu options
            print("  MAIN MENU")
            self.print_divider()
            print("  1.  🚀  Start Quiz")
            print("  2.  📊  View Score History")
            print("  3.  📈  Performance Analysis")
            print("  4.  🚪  Exit & Reset")
            self.print_divider()

            # Get user's menu choice (must be 1, 2, 3, or 4)
            choice = self.get_valid_input("\n  Enter choice (1-4): ", ["1", "2", "3", "4"])

            # Route to the right function based on choice
            if choice == "1":
                self.setup_quiz()    # go to quiz setup
            elif choice == "2":
                self.show_history()  # go to history screen
            elif choice == "3":
                self.show_analysis() # go to analysis screen
            elif choice == "4":
                self.exit_app()      # exit the app
                break                # stop the loop


    # ==========================================
    #  QUIZ SETUP
    #  Player enters name, picks difficulty
    #  Like: screen-setup in JS
    # ==========================================
    def setup_quiz(self):
        self.clear_screen()
        self.print_header()
        print("  NEW QUIZ SETUP")
        self.print_divider()

        # --- Input Validation: Player Name ---
        while True:
            name = input("\n  Enter your name: ").strip()
            if name:                   # name is not empty
                self.player_name = name
                break
            else:
                print("  ⚠️  Name cannot be empty! Please enter your name.")

        # --- Difficulty Selection ---
        print("\n  Choose Difficulty:")
        self.print_divider()
        print("  1.  🌱  Easy    (5 questions)")
        print("  2.  ⚡  Medium  (5 questions)")
        print("  3.  🔥  Hard    (5 questions)")
        print("  4.  🎲  Mixed   (10 random questions)")

        diff_choice = self.get_valid_input(
            "\n  Enter difficulty (1-4): ",
            ["1", "2", "3", "4"]
        )

        # Map number choice to difficulty string
        diff_map = {
            "1": "easy",
            "2": "medium",
            "3": "hard",
            "4": "mixed"
        }
        self.selected_diff = diff_map[diff_choice]

        # --- Negative Marking Toggle ---
        print("\n  ⚠️  Enable Negative Marking?")
        print("     (Deduct 0.25 marks for each wrong answer)")
        neg_choice = self.get_valid_input(
            "  Enter (y/n): ",
            ["y", "n", "Y", "N"]
        )
        # True if user typed y or Y, False otherwise
        self.negative_marking = neg_choice.lower() == "y"

        # --- Show what was selected ---
        print(f"\n  ✅ Name       : {self.player_name}")
        print(f"  ✅ Difficulty  : {self.selected_diff.capitalize()}")
        print(f"  ✅ Neg. Marking: {'ON ⚠️' if self.negative_marking else 'OFF'}")

        input("\n  Press Enter to start the quiz...")

        # Start the quiz!
        self.start_quiz()


    # ==========================================
    #  START QUIZ
    #  Selects questions and resets all counters
    #  Like: startQuiz() in JS
    # ==========================================
    def start_quiz(self):
        # --- Select questions based on difficulty ---
        if self.selected_diff == "mixed":
            # Mixed: shuffle everything and take 10
            pool = self.shuffle_list(self.all_questions)
            self.active_questions = pool[:10]
        else:
            # Filter by difficulty, shuffle, take 5
            pool = [q for q in self.all_questions
                    if q["difficulty"] == self.selected_diff]
            pool = self.shuffle_list(pool)
            self.active_questions = pool[:5]

        # Make sure we have questions
        if not self.active_questions:
            print("❌ No questions found for this difficulty!")
            input("Press Enter to go back...")
            return

        # --- Reset all score counters ---
        self.current_index  = 0
        self.score          = 0.0
        self.correct_count  = 0
        self.wrong_count    = 0
        self.skipped_count  = 0
        self.penalty_total  = 0.0

        # --- Run through all questions ---
        # Loop through each question one by one
        for i in range(len(self.active_questions)):
            self.current_index = i
            result = self.show_question()  # show question, get result

            # If player chose to quit mid-quiz
            if result == "quit":
                print("\n  Quiz abandoned.")
                input("  Press Enter to return to menu...")
                return

        # All questions done — show results
        self.show_results()


    # ==========================================
    #  SHOW QUESTION
    #  Displays one question and handles answer
    #  Like: loadQuestion() + checkAnswer() in JS
    # ==========================================
    def show_question(self):
        self.clear_screen()
        self.print_header()

        # Get the current question dictionary
        q = self.active_questions[self.current_index]
        total = len(self.active_questions)

        # --- Progress Bar ---
        # Calculate how far through the quiz we are
        done = self.current_index          # questions completed
        bar_len = 30                       # total bar characters
        filled = int((done / total) * bar_len)  # how many to fill
        bar = "█" * filled + "░" * (bar_len - filled)

        # Display progress
        print(f"  Question {self.current_index + 1}/{total}  [{bar}]")
        print(f"  Score: {self.score:.2f}  |  "
              f"✅ {self.correct_count}  ❌ {self.wrong_count}  "
              f"⏭️  {self.skipped_count}")
        self.print_divider()

        # --- Difficulty Badge ---
        diff_icons = {"easy": "🌱", "medium": "⚡", "hard": "🔥"}
        icon = diff_icons.get(q["difficulty"], "❓")
        print(f"  {icon} {q['difficulty'].upper()}  |  {q['category']}\n")

        # --- Question Text ---
        # Print question, wrapping long lines manually
        print(f"  Q: {q['question']}\n")

        # --- Answer Options ---
        labels = ["A", "B", "C", "D"]
        for i, option_text in enumerate(q["options"]):
            print(f"     {labels[i]}.  {option_text}")

        self.print_divider()

        # --- Timer Setup ---
        # We use a threading.Event to signal when time is up
        # This is the Python equivalent of setInterval() in JS
        self.answered      = False
        self.timer_expired = False
        stop_event         = threading.Event()  # signal to stop timer

        # This function runs in a background thread (counts down)
        def run_timer():
            for seconds_left in range(30, 0, -1):  # 30 down to 1
                if stop_event.is_set():
                    # Main thread told us to stop (player answered)
                    return
                # Print timer on same line (overwrite with \r)
                print(f"\r  ⏱️  Time left: {seconds_left:2d}s  "
                      f"| Enter A/B/C/D or Q to quit: ", end="", flush=True)
                time.sleep(1)  # wait 1 second

            # If we reach here, time ran out without player answering
            if not stop_event.is_set():
                self.timer_expired = True
                # Print a newline so output looks clean
                print(f"\r  ⏱️  Time's up! ⏰                              ")

        # Start timer thread (daemon=True means it stops if main program exits)
        timer = threading.Thread(target=run_timer, daemon=True)
        timer.start()

        # --- Get Player's Answer ---
        # input() blocks until the player types something
        user_input = input("").strip().upper()

        # Signal the timer thread to stop
        stop_event.set()
        timer.join(timeout=1)  # wait for timer thread to finish

        print()  # blank line for spacing

        # --- Handle Timeout ---
        if self.timer_expired and user_input not in ["A", "B", "C", "D"]:
            self.skipped_count += 1
            correct_letter = labels[q["answer"]]
            correct_text   = q["options"][q["answer"]]
            print(f"  ⏰ Time's up! The correct answer was:")
            print(f"     {correct_letter}. {correct_text}")
            print(f"  💡 {q['explanation']}")
            input("\n  Press Enter for next question...")
            return "next"  # move to next question

        # --- Handle Quit ---
        if user_input == "Q":
            return "quit"

        # --- Validate Input ---
        # Keep asking until valid answer is given (A, B, C, D)
        while user_input not in ["A", "B", "C", "D"]:
            user_input = input("  ⚠️  Enter A, B, C, or D: ").strip().upper()

        # Convert letter to index: A=0, B=1, C=2, D=3
        selected_index = labels.index(user_input)

        # --- Check Answer ---
        if selected_index == q["answer"]:
            # ✅ Correct!
            self.correct_count += 1
            self.score         += 1
            print("  ✅ CORRECT! +1 mark")

        else:
            # ❌ Wrong
            self.wrong_count += 1
            correct_letter    = labels[q["answer"]]
            correct_text      = q["options"][q["answer"]]

            if self.negative_marking:
                # Deduct 0.25 marks
                self.score         -= 0.25
                self.penalty_total += 0.25
                print(f"  ❌ WRONG! -0.25 marks (negative marking)")
            else:
                print("  ❌ WRONG! No marks deducted.")

            print(f"     Correct answer: {correct_letter}. {correct_text}")

        # Always show the explanation
        print(f"  💡 {q['explanation']}")
        print(f"     Current Score: {self.score:.2f}")

        input("\n  Press Enter for next question...")
        return "next"  # move on


    # ==========================================
    #  SHOW RESULTS
    #  Displays final score and performance rank
    #  Like: endQuiz() / screen-results in JS
    # ==========================================
    def show_results(self):
        self.clear_screen()
        self.print_header()

        total      = len(self.active_questions)
        percentage = max(0, (self.score / total) * 100)  # 0–100%

        # --- Determine Rank ---
        # Same thresholds as in JavaScript version
        if percentage >= 90:
            rank     = "Expert"
            emoji    = "🏆"
            feedback = (f"Outstanding performance, {self.player_name}! "
                        f"You've mastered Python at this level.")
        elif percentage >= 70:
            rank     = "Advanced"
            emoji    = "🌟"
            feedback = (f"Great work, {self.player_name}! You have strong "
                        f"Python knowledge. Review a few missed topics.")
        elif percentage >= 45:
            rank     = "Intermediate"
            emoji    = "📚"
            feedback = (f"Good effort, {self.player_name}! Practice loops, "
                        f"functions, and data structures to improve.")
        else:
            rank     = "Beginner"
            emoji    = "🌱"
            feedback = (f"Keep going, {self.player_name}! Review Python "
                        f"basics and try again. Every expert was once a beginner!")

        # --- Print Results ---
        print(f"  {emoji}  QUIZ COMPLETE — {rank.upper()}!")
        self.print_divider()
        print(f"  Player    : {self.player_name}")
        print(f"  Difficulty: {self.selected_diff.capitalize()}")
        print(f"  Neg.Marks : {'ON' if self.negative_marking else 'OFF'}")
        self.print_divider()

        # Big score display
        print(f"\n       FINAL SCORE:  {self.score:.2f} / {total}")
        print(f"       PERCENTAGE :  {percentage:.1f}%\n")

        # Stats row
        self.print_divider()
        print(f"  ✅ Correct : {self.correct_count}")
        print(f"  ❌ Wrong   : {self.wrong_count}", end="")
        if self.negative_marking and self.penalty_total > 0:
            print(f"  (penalty: -{self.penalty_total:.2f})")
        else:
            print()
        print(f"  ⏭️  Skipped : {self.skipped_count}")
        self.print_divider()

        # Accuracy calculation
        answered = self.correct_count + self.wrong_count
        if answered > 0:
            accuracy = round((self.correct_count / answered) * 100)
            print(f"  Accuracy  : {accuracy}%  (answered questions only)")
            self.print_divider()

        # Personalized feedback
        print(f"\n  {emoji} RANK: {rank}")
        print(f"  {feedback}\n")

        # --- Save this result ---
        result = {
            "name"      : self.player_name,
            "score"     : self.score,
            "total"     : total,
            "percentage": round(percentage, 1),
            "correct"   : self.correct_count,
            "wrong"     : self.wrong_count,
            "skipped"   : self.skipped_count,
            "difficulty": self.selected_diff,
            "rank"      : rank,
            "negative"  : self.negative_marking,
            "penalty"   : self.penalty_total,
            "date"      : datetime.now().strftime("%d/%m/%Y %H:%M")
        }

        self.score_history.append(result)
        self.save_history()  # write to JSON file

        input("  Press Enter to return to menu...")


    # ==========================================
    #  SHOW HISTORY
    #  Lists all past quiz attempts
    #  Like: renderHistory() / screen-history in JS
    # ==========================================
    def show_history(self):
        self.clear_screen()
        self.print_header()
        print("  SCORE HISTORY")
        self.print_divider()

        if not self.score_history:
            # No attempts yet
            print("\n  📋 No quiz attempts yet.")
            print("     Play your first quiz to see history here!\n")
        else:
            # Show most recent first (reverse the list)
            reversed_history = list(reversed(self.score_history))

            # Print each result
            for i, r in enumerate(reversed_history, start=1):
                neg_flag = " ⚠️" if r.get("negative") else ""
                print(f"  {i:2}. {r['name']:<15} "
                      f"{r['score']:.2f}/{r['total']}  "
                      f"({r['percentage']}%)  "
                      f"{r['difficulty'].upper():<8}  "
                      f"{r['rank']:<12}  "
                      f"{r['date']}{neg_flag}")

        self.print_divider()
        input("\n  Press Enter to return to menu...")


    # ==========================================
    #  SHOW ANALYSIS
    #  Detailed stats across ALL attempts
    #  Like: renderAnalysis() / screen-analysis in JS
    # ==========================================
    def show_analysis(self):
        self.clear_screen()
        self.print_header()
        print("  PERFORMANCE ANALYSIS")
        self.print_divider()

        if not self.score_history:
            print("\n  📈 No data yet.")
            print("     Complete at least one quiz to see analysis!\n")
            self.print_divider()
            input("\n  Press Enter to return to menu...")
            return

        # --- Calculate totals across all attempts ---
        total_attempts = len(self.score_history)
        total_correct  = 0
        total_wrong    = 0
        total_skipped  = 0
        total_score    = 0.0
        total_possible = 0

        # Track how many times each rank was achieved
        rank_counts = {"Beginner": 0, "Intermediate": 0,
                       "Advanced": 0, "Expert": 0}

        for r in self.score_history:
            total_correct  += r["correct"]
            total_wrong    += r["wrong"]
            total_skipped  += r["skipped"]
            total_score    += r["score"]
            total_possible += r["total"]

            # Count rank occurrences
            if r["rank"] in rank_counts:
                rank_counts[r["rank"]] += 1

        total_answered = total_correct + total_wrong + total_skipped
        accuracy  = round((total_correct / total_answered) * 100) if total_answered > 0 else 0
        avg_score = total_score / total_attempts

        # Determine best rank achieved
        best_rank = "Beginner"
        if rank_counts["Expert"]       > 0: best_rank = "Expert"
        elif rank_counts["Advanced"]   > 0: best_rank = "Advanced"
        elif rank_counts["Intermediate"]>0: best_rank = "Intermediate"

        # --- Print Summary ---
        print(f"\n  Total Attempts : {total_attempts}")
        print(f"  Avg Score      : {avg_score:.2f}")
        print(f"  Accuracy       : {accuracy}%")
        print(f"  Best Rank      : {best_rank}")
        self.print_divider()

        # --- Answer Breakdown with visual bars ---
        print("\n  ANSWER BREAKDOWN")
        print()

        bar_width = 25  # width of the progress bar

        def make_bar(count, total_val, symbol):
            # Build a visual bar like: [████░░░░░░] 12 (60%)
            if total_val == 0:
                pct = 0
            else:
                pct = count / total_val
            filled = int(pct * bar_width)
            bar    = "█" * filled + "░" * (bar_width - filled)
            return f"  [{bar}] {count} ({round(pct*100)}%)"

        print(f"  ✅ Correct  {make_bar(total_correct,  total_answered, '✅')}")
        print(f"  ❌ Wrong    {make_bar(total_wrong,    total_answered, '❌')}")
        print(f"  ⏭️  Skipped  {make_bar(total_skipped,  total_answered, '⏭️ ')}")

        self.print_divider()

        # --- Rank Distribution ---
        print("\n  RANK DISTRIBUTION")
        print()
        for rank_name, count in rank_counts.items():
            times = "time" if count == 1 else "times"
            print(f"  {rank_name:<14} : {count} {times}")

        self.print_divider()
        input("\n  Press Enter to return to menu...")


    # ==========================================
    #  EXIT APP
    #  Clears all history and exits
    #  Like: exitApp() in JS
    # ==========================================
    def exit_app(self):
        self.clear_screen()
        self.print_header()
        print("  EXIT & RESET")
        self.print_divider()
        print("\n  ⚠️  This will delete ALL your saved history.")
        print("     Are you sure?\n")

        # Ask for confirmation
        confirm = self.get_valid_input(
            "  Type 'yes' to confirm or 'no' to cancel: ",
            ["yes", "no"]
        )

        if confirm == "yes":
            # Clear in-memory history
            self.score_history = []

            # Delete the history file if it exists
            if os.path.exists(self.history_file):
                os.remove(self.history_file)

            print("\n  ✅ All data cleared! Goodbye 👋")
            time.sleep(1.5)
            exit()  # quit the program

        else:
            print("\n  Cancelled. Returning to menu...")
            time.sleep(1)


# ==============================================
#  ENTRY POINT
#  This block runs when you execute: python app.py
#  Like: window.addEventListener('DOMContentLoaded', ...)
# ==============================================
if __name__ == "__main__":
    # Create the app object (calls __init__ automatically)
    app = QuizApp()

    # Start the main menu loop
    app.show_menu()
