import numpy as np
import matplotlib.pyplot as plt
import copy
import time
N_OPP = 3
INITIAL_N_CARDS = 10
rng = np.random.default_rng(seed=42)

lookupTable = [0] * 105   # indices 0..104, ignore index 0
for c in range(1, 105):
    if c == 55:
        lookupTable[c] = 7
    elif c % 11 == 0:
        lookupTable[c] = 5
    elif c % 10 == 0:
        lookupTable[c] = 3
    elif c % 5 == 0:
        lookupTable[c] = 2
    else:
        lookupTable[c] = 1
lookupTable = np.array(lookupTable)


class GameState:
    def __print__(self):
        print("Board:",self.board)
        print("My hand:",self.my_hand)
        print("Unrevealed cards:",self.unrevealed_Cards)
        print("Accumulated bulls:", self.scores)
 
    def __init__(self):
        self.unrevealed_Cards = np.arange(1,104+1, dtype=np.int8)
        self.rounds_played = 0
        self.scores = np.zeros(N_OPP+1)

        self.my_hand = list(map(int,input("Input hand:").split()))
        self.shrinkUnrevealedCards(self.my_hand)
        initial_board_cards = list(map(int,input("Init board:").split()))
        self.shrinkUnrevealedCards(initial_board_cards)

        self.board = np.zeros(shape=(4,3), dtype=np.int8) #four rows x bulls,cards,face 
        self.board[:,2] = initial_board_cards
        self.board[:,1] = 1
        self.board[:,0] = lookupTable[initial_board_cards]
    #Don't need to shrink here
    def initializeRandomHands(self):
        self.hands = rng.choice(self.unrevealed_Cards, size=(N_OPP,INITIAL_N_CARDS-self.rounds_played), replace=False).tolist()
        # self.shrinkUnrevealedCards(self.hands)

    def shrinkUnrevealedCards(self, cards):
        self.unrevealed_Cards = self.unrevealed_Cards[~np.isin(self.unrevealed_Cards,cards)]

    #returns index of the largest face that is smaller than 'card' 
    def findLargestSmaller(self, card):
        largest_smaller_index = -1
        largest_smaller_value = -1
        for i in range(4): #four rows in board
            face = self.board[i,2]
            if face < card:
                if face > largest_smaller_value:
                    largest_smaller_value = face
                    largest_smaller_index = i
        return largest_smaller_index
    
    def findLargestSmallerColumn(self, card):
        largest_smaller_index = -1
        largest_smaller_value = -1
        for i in range(4): #four rows in board
            face = self.board[i,2]
            if face < card:
                if face > largest_smaller_value:
                    largest_smaller_value = face
                    largest_smaller_index = i

        if largest_smaller_index == -1:
            return 6
        
        return self.board[largest_smaller_index,2]
    
    def findSmallestBullSum(self):
        smallest_index = -1
        smallest_value = 100
        for i in range(4):
            bull_sum = self.board[i,0]
            if bull_sum < smallest_value:
                smallest_value = bull_sum
                smallest_index = i
        return smallest_index

    def lay(self, card, simulation: bool):
        row_idx = self.findLargestSmaller(card)

        penalty = 0
        
        if row_idx==-1:
            if simulation:
                row_idx = self.findSmallestBullSum()
            else:
                row_idx = int(input(f"input which row was taken by {card}:"))
            row = self.board[row_idx]
            penalty = row[0]
            row[0] = lookupTable[card]
            row[1] = 1
            row[2] = card
        else:
            row = self.board[row_idx]
            if row[1] == 5:
                penalty = row[0]
                row[0] = lookupTable[card]
                row[1] = 1
            else:
                row[0] += lookupTable[card]
                row[1] += 1
            row[2] = card

        return penalty
    
    def reveal(self, cards, simulation:bool):
        scores = np.zeros(N_OPP+1)
        player_card = cards[0]
        sorted_cards = sorted(cards)
        for i in range(len(sorted_cards)):           
            penalty = self.lay(sorted_cards[i], simulation=simulation)
            if sorted_cards[i] == player_card:
                scores[0] = penalty
            else:
                for player_id in range(1,N_OPP+1):
                    if cards[player_id] == sorted_cards[i]:
                        scores[player_id] = penalty    

        if not simulation:
            self.shrinkUnrevealedCards(cards)

        #removes the card that you played from your hand
        self.my_hand.remove(player_card)

        if simulation:
            for i in range(0, len(self.hands)):
                self.hands[i].remove(cards[i+1]) #card 0 is player, so card 1 corresponds to opp 0


        self.scores += scores
        self.rounds_played += 1
    
    #Some pretty bad heuristics
    def heuristicLowest(self, hand):        
        return (hand == np.min(hand)).astype(int)

    def heuristicCloseness(self, hand):
        conditions = np.zeros_like(hand)
        for i in range(len(hand)):
            if ((self.board[:,2] < hand[i]) & (self.board[:,2] + 5 > hand[i])).sum():
                conditions[i] = 1
        return conditions
            
    def heuristicSafe(self, hand):
        conditions = np.zeros_like(hand)
        for i in range(len(hand)):
            if self.findLargestSmallerColumn(hand[i]) <= 2:
                conditions[i] = 1
        return conditions

    def heuristicLowEatCost(self, hand):
        conditions = np.zeros_like(hand)
        for i in range(len(hand)):
            if np.all(hand[i] < self.board[:,2]) and np.min(self.board[:,0])==1:
                conditions[i]=1
        return conditions
    
    def applyHeuristics(self, hand):
        return np.argmax(self.heuristicCloseness(hand)+
                         self.heuristicLowEatCost(hand)+
                         self.heuristicLowest(hand)+
                         self.heuristicSafe(hand))
    
    def montecarlo(self):
        if self.rounds_played==10:
            return

        rounds_left = 10 - self.rounds_played

        M = 30000//rounds_left
        
        for card in self.my_hand:
            simulated_scores = np.zeros(shape=(M,1+N_OPP))
            for m in range(M):
                simulated_scores[m]=self.singleSimulation(card)

            print(f"Card: {card}, mean: {simulated_scores[:,0].mean()}, std: {simulated_scores[:,0].std()}, first place (%): {100*((np.argmin(simulated_scores, axis=1)==0).sum()/M)}")
            # plt.figure()
            # plt.title(f"Card: {card}, mean: {simulated_scores[:,0].mean()}, std: {simulated_scores[:,0].std()}")
            # plt.hist(simulated_scores[:,0])
            # plt.show(block=False)

    #Assumes at most 9 rounds played
    def singleSimulation(self, card):
        gs_copy = copy.deepcopy(self)
        gs_copy.initializeRandomHands()
        # print("Doing a single simulation")
        # print("The initialized hands are:")
        # print(gs_copy.hands)      

        cards = [card]
        for i in range(N_OPP):
            cards.append(gs_copy.hands[i][gs_copy.applyHeuristics(gs_copy.hands[i])])
        # print("The cards that are going to be played by heur:", cards)
        gs_copy.reveal(cards, simulation=True)

        while(gs_copy.rounds_played != 10):
            cards = [gs_copy.my_hand[gs_copy.applyHeuristics(gs_copy.my_hand)]]
            for i in range(N_OPP):
                cards.append(gs_copy.hands[i][gs_copy.applyHeuristics(gs_copy.hands[i])])
            # print("The cards that are going to be played by heur:", cards)
            gs_copy.reveal(cards, simulation=True)
            # print("Round: ", gs_copy.rounds_played)
            # gs_copy.__print__()
            # print("Hands: ",gs_copy.hands)      
         
        return gs_copy.scores





    
def main():
    gs = GameState()
    gs.__print__()
    while(gs.rounds_played != 10):
        gs.montecarlo()
        cards_played = list(map(int,input("Input which cards are played: (player,opp1,opp2,opp3,...)").split()))
        gs.reveal(cards=cards_played, simulation=False)
        gs.__print__()
        print("Here is the actual current boardstate again:")
        gs.__print__()


if __name__ == "__main__":
    main()
