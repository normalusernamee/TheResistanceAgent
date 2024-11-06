import pkgutil, importlib, inspect, random, math
from game import Game
from agent import Agent
from agent_handler import AgentHandler

# Number of tournaments to run
NUMBER_OF_TOURNAMENTS = 10
NUMBER_OF_GAMES = 1000  # Games per tournament
PRINT_GAME_EVENTS = False  # Set this to True if you want to see game events
LEADERBOARD_LINES = 50
LEADERBOARD_WIDTH = 200
IGNORE_AGENTS = []

# Variables for agent details and scores
agent_name_length = 0
agent_fullname_length = 0
agent_classes = []
agent_pool = []
agent_class_names = set()
agent_class_fullnames = {}
duplicates_exist = False

# Find and load agents from the agents folder
for item in pkgutil.iter_modules(["agents"]):
    package_name = f"agents.{item.name}"
    package = importlib.import_module(package_name)
    for name, cls in inspect.getmembers(package, inspect.isclass):
        if issubclass(cls, Agent) and cls is not Agent:
            if name in IGNORE_AGENTS:
                continue
            if name in agent_class_names:
                duplicates_exist = True
            agent_class_names.add(name)
            print(f"Found agent: {name}")
            agent_classes.append(cls)
            if len(name) > agent_name_length:
                agent_name_length = len(name)
            fullname = cls.__module__ + "." + cls.__name__
            agent_class_fullnames[cls] = fullname
            if len(fullname) > agent_fullname_length:
                agent_fullname_length = len(fullname)

# Function to create agents
def create_agent(agent_cls):
    agent_name = f"{agent_cls.__name__[:3].lower()}{len(agent_pool)}"
    agent = agent_cls(name=agent_name)
    agent = AgentHandler(agent)
    agent.orig_class = agent_cls
    return agent

# Function to print leaderboard
def print_leaderboard(scores, tournament_num=None):
    leaderboard = []
    for agent_cls in agent_classes:
        agent_scores = scores[agent_cls]
        win_rate = agent_scores["wins"] / agent_scores["games"] if agent_scores["games"] else 0
        res_win_rate = agent_scores["res_wins"] / agent_scores["res"] if agent_scores["res"] else 0
        spy_win_rate = agent_scores["spy_wins"] / agent_scores["spy"] if agent_scores["spy"] else 0
        if duplicates_exist:
            agent_name = f"{agent_class_fullnames[agent_cls]:<{agent_fullname_length}}"
        else:
            agent_name = f"{agent_cls.__name__:<{agent_name_length}}"
        leaderboard_line = (
            f"{agent_name} | win_rate={win_rate:.4f} res_win_rate={res_win_rate:.4f} spy_win_rate={spy_win_rate:.4f} | " +
            " ".join(f"{key}={agent_scores[key]}" for key in agent_scores)
        )
        leaderboard.append((-win_rate, leaderboard_line, agent_cls))
    leaderboard.sort()
    leaderboard = leaderboard[:LEADERBOARD_LINES]
    
    if tournament_num is not None:
        print(f"\nLEADERBOARD AFTER TOURNAMENT {tournament_num + 1}")
    print(f"Resistance Wins: {scores['res_wins']}, Spy Wins: {scores['spy_wins']}, Resistance Win Rate: {scores['res_wins'] / scores['games']:.4f}")
    for i, item in enumerate(leaderboard):
        _, line, _ = item
        print(f"{i+1:2}: {line[:LEADERBOARD_WIDTH]}")
    
    # Return the best agent for the current tournament
    return leaderboard[0][2]

# Function to run one tournament
def run_one_tournament():
    # Create agents for the tournament
    number_of_duplicates = math.ceil(10 / len(agent_classes))
    for agent_cls in agent_classes:
        for i in range(number_of_duplicates):
            agent_pool.append(create_agent(agent_cls))
    
    # Initialize scores
    scores = {agent_cls: {
        "errors": 0,
        "games": 0, "wins": 0, "losses": 0, "res": 0, "spy": 0,
        "res_wins": 0, "res_losses": 0, "spy_wins": 0, "spy_losses": 0,
    } for agent_cls in agent_classes}
    scores["games"] = 0
    scores["res_wins"] = 0
    scores["spy_wins"] = 0
    
    # Run games for the tournament
    for game_num in range(NUMBER_OF_GAMES):
        number_of_players = random.randint(5, 10)
        agents = random.sample(agent_pool, number_of_players)
        game = Game(agents)
        game.play()
        resistance_victory, winning_team, losing_team = game.get_results()
        scores["games"] += 1
        if resistance_victory:
            scores["res_wins"] += 1
        else:
            scores["spy_wins"] += 1
        for agent in agents:
            agent_scores = scores[agent.orig_class]
            agent_scores["games"] += 1
            agent_scores["errors"] += agent.errors
            agent.reset_error_counter()
        for agent in winning_team:
            agent_scores = scores[agent.orig_class]
            agent_scores["wins"] += 1
            if resistance_victory:
                agent_scores["res"] += 1
                agent_scores["res_wins"] += 1
            else:
                agent_scores["spy"] += 1
                agent_scores["spy_wins"] += 1
        for agent in losing_team:
            agent_scores = scores[agent.orig_class]
            agent_scores["losses"] += 1
            if resistance_victory:
                agent_scores["spy"] += 1
                agent_scores["spy_losses"] += 1
            else:
                agent_scores["res"] += 1
                agent_scores["res_losses"] += 1
    
    return scores

# Run multiple tournaments and combine results
overall_scores = {agent_cls: {
    "errors": 0,
    "games": 0, "wins": 0, "losses": 0, "res": 0, "spy": 0,
    "res_wins": 0, "res_losses": 0, "spy_wins": 0, "spy_losses": 0,
} for agent_cls in agent_classes}
overall_scores["games"] = 0
overall_scores["res_wins"] = 0
overall_scores["spy_wins"] = 0

# Track how many tournaments each agent wins
tournament_wins = {agent_cls: 0 for agent_cls in agent_classes}

for tournament_num in range(NUMBER_OF_TOURNAMENTS):
    print(f"\nRunning Tournament {tournament_num + 1}...\n")
    tournament_scores = run_one_tournament()
    
    # Accumulate scores from the tournament into overall scores
    for agent_cls in agent_classes:
        for key in tournament_scores[agent_cls]:
            overall_scores[agent_cls][key] += tournament_scores[agent_cls][key]
    overall_scores["games"] += tournament_scores["games"]
    overall_scores["res_wins"] += tournament_scores["res_wins"]
    overall_scores["spy_wins"] += tournament_scores["spy_wins"]
    
    # Print leaderboard and track the winning agent
    best_agent = print_leaderboard(tournament_scores, tournament_num)
    tournament_wins[best_agent] += 1

# Final overall leaderboard
print("\nFINAL OVERALL LEADERBOARD")
print_leaderboard(overall_scores)

# Find the agent with the most tournament wins
best_overall_agent = max(tournament_wins, key=tournament_wins.get)
best_win_rate = overall_scores[best_overall_agent]["wins"] / overall_scores[best_overall_agent]["games"]

print(f"\nMost successful agent: {best_overall_agent.__name__}")
print(f"Win rate: {best_win_rate:.4f}")
print(f"Tournaments won: {tournament_wins[best_overall_agent]}")

print("\nTournament wins breakdown:")
for agent_cls, wins in tournament_wins.items():
    print(f"{agent_cls.__name__}: {wins} tournament wins")
