from agent import Agent
import random

class MyVerySmartAgent(Agent):        
    '''A sample implementation of a random agent in the game The Resistance'''

    def __init__(self, name='Special'):
        '''Initializes the agent.'''
        self.name = name
        self.current_round = 0  # Track the current round

    def new_game(self, number_of_players, player_number, spy_list):
        '''Initializes the game parameters.'''
        self.number_of_players = number_of_players
        self.player_number = player_number
        self.spy_list = spy_list
        self.mission_history = []  # To store outcomes of previous missions
        self.vote_history = {}     # To track who proposed missions and their outcomes
        self.suspicion_scores = {i: 1 for i in range(number_of_players)}  # Dictionary with suspicion score of 1 for each player


        self.leeway = 1.5 # reduce leeway to become less tolerant of suspicious behaviour


        
    def is_spy(self):
        '''Returns True iff the agent is a spy.'''
        return self.player_number in self.spy_list

    def propose_mission(self, team_size, betrayals_required):
        team = []

        if self.is_spy():
            # Add yourself to the team
            team.append(self.player_number)

            # Get list of other spies
            other_spies = [(spy, self.suspicion_scores[spy]) for spy in self.spy_list if spy != self.player_number]
            other_spies.sort(key=lambda x: x[1])  # Sort by suspicion score 

            # Add spies with the least suspicion, up to the required number of betrayals
            for spy, _ in other_spies:
                if len(team) < betrayals_required:
                    team.append(spy)

            # Fill the rest of the team with high-suspicion non-spy players to divert attention
            non_spy_players = [(player, self.suspicion_scores[player]) for player in range(self.number_of_players)
                               if player not in self.spy_list]
            non_spy_players.sort(key=lambda x: x[1], reverse=True)  # Sort by suspicion 

            # add players with high-suspicion score (non spies)
            for player, _ in non_spy_players:
                if len(team) < team_size and player not in team:
                    team.append(player)

        else:
            # Resistance: Add yourself and trusted players based on suspicion scores
            team.append(self.player_number)
            
            # Add the least suspicious players to the team
            non_spy_players = [(player, self.suspicion_scores[player]) for player in range(self.number_of_players)
                               if player != self.player_number]
            non_spy_players.sort(key=lambda x: x[1])  # Sort by suspicion score 

            for player, _ in non_spy_players:
                if len(team) < team_size:
                    team.append(player)

        return team

    def vote(self, mission, proposer, betrayals_required):
        '''Determines whether to vote for the mission based on suspicion scores and spy coordination.'''
        if self.is_spy():
            # Count how many spies are on the mission
            spy_count = sum([1 for agent in mission if agent in self.spy_list])

            # approve missions that you know will fail
            if spy_count >= betrayals_required:
                return True
            
            # reject missions that you know will succeed
            return False
            
        else:
            
            # As a Resistance member, determine whether to approve or reject the mission
            suspicion_sum = sum(self.suspicion_scores[player] for player in mission)  # Sum of suspicion scores of players on the mission
            threshold = len(mission)  # threshold based on the number of players on the mission
        
         
            
            # If the sum of suspicion scores exceeds the threshold, reject the mission
            if suspicion_sum - self.leeway > threshold: # take less risk towards the end rounds with leeway
                return False  # Too suspicious, reject the mission
            
            return True  # Approve mission if no player is too suspicious
    

    def vote_outcome(self, mission, proposer, votes):
        '''
        mission is a list of agents to be sent on a mission. 
        The agents on the mission are distinct and indexed between 0 and number_of_players.
        proposer is an int between 0 and number_of_players and is the index of the player who proposed the mission.
        votes (not a dictionary, its a list with players that voted) is a dictionary mapping player indexes to Booleans (True if they voted for the mission, False otherwise).
        No return value is required or expected.
        '''
            # Initialize the record for this voting outcome
        voting_record = {
            'mission': mission,
            'proposer': proposer,
            'votes_for': [],
            'votes_against': [],
            'outcome': None  
        }
        
        # Determine who voted for and against the mission
        for player in range(self.number_of_players):
            if player in votes:  # Check if the player voted and if they voted for the mission
                voting_record['votes_for'].append(player)
            else:
                voting_record['votes_against'].append(player)
        
        # Determine the outcome of the vote
        if len(voting_record['votes_for']) > len(voting_record['votes_against']):
            voting_record['outcome'] = True  # Mission approved
        else:
            voting_record['outcome'] = False  # Mission rejected
        
        # Store the voting record in self.vote_history
        self.vote_history[(self.current_round, proposer)] = voting_record



    def betray(self, mission, proposer, betrayals_required):
        '''Decides whether to betray the mission based on spy requirements.'''
        if self.is_spy():
            spies_on_mission = [agent for agent in mission if agent in self.spy_list]

            if len(spies_on_mission) >= betrayals_required:
                return True  # Fail the mission
            else:
                return False

        return False  # Non-spies cannot betray

    def mission_outcome(self, mission, proposer, num_betrayals, mission_success):
        '''
        mission is a list of agents to be sent on a mission. 
        The agents on the mission are distinct and indexed between 0 and number_of_players.
        proposer is an int between 0 and number_of_players and is the index of the player who proposed the mission.
        num_betrayals is the number of people on the mission who betrayed the mission, 
        and mission_success is True if there were not enough betrayals to cause the mission to fail, False otherwise.
        It is not expected or required for this function to return anything.
        '''
        if mission_success:
            # Mission succeeded: Decrease suspicion for players on the mission
            for player in mission:
                self.suspicion_scores[player] = max(0, self.suspicion_scores[player] - 1)  # Ensure suspicion doesn't go below 0
                # Update suspicion scores based on votes for this mission
                # Decrease suspicion for the proposer
                self.suspicion_scores[proposer] = max(0, self.suspicion_scores[proposer] - 0.8)  # Ensure suspicion doesn't go below 0
            voting_record = self.vote_history.get((self.current_round, proposer), None)
            if voting_record:
                for player in voting_record['votes_against']:
                    # Increase suspicion for players who voted against a successful mission
                    self.suspicion_scores[player] += 0.5  # Increase suspicion score
                for player in voting_record['votes_for']:
                    # Increase suspicion for players who voted against a successful mission
                    self.suspicion_scores[player] -= 0.3  # Increase suspicion score
                
        else:
            # Mission failed: Increase suspicion for all players on the mission
            for player in mission:
                self.suspicion_scores[player] += 1
            # Increase suspicion for the proposer
            self.suspicion_scores[proposer] += 0.5

            voting_record = self.vote_history.get((self.current_round, proposer), None)
            for player in voting_record['votes_against']:
                self.suspicion_scores[player] -= 1
            for player in voting_record['votes_for']:
                self.suspicion_scores[player] += 1
                
        self.mission_history.append((mission, proposer, num_betrayals, mission_success))

        
    def round_outcome(self, rounds_complete, missions_failed):
        '''
        basic informative function, where the parameters indicate:
        rounds_complete, the number of rounds (0-5) that have been completed
        missions_failed, the numbe of missions (0-3) that have failed.
        '''
        self.leeway = self.leeway - 0.4 # Decrease leeway slightly each round

        
    
    def game_outcome(self, spies_win, spies):
        '''
        basic informative function, where the parameters indicate:
        spies_win, True iff the spies caused 3+ missions to fail
        spies, a list of the player indexes for the spies.
        '''

        pass
