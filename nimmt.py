import numpy as np
import copy
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
        print(self.board)
        print(self.my_hand)
        print(self.unrevealed_Cards)
 
    def __init__(self, game_mode):
        self.game_mode = game_mode
        self.unrevealed_Cards = np.arange(1,104+1, dtype=np.int8)
        self.rounds_played = 0

        if self.game_mode == 0:
            self.my_hand = list(map(int,input("Input hand:").split()))
            self.shrinkUnrevealedCards(self.my_hand)
            initial_board_cards = list(map(int,input("Init board:").split()))
            self.shrinkUnrevealedCards(initial_board_cards)
        elif self.game_mode == 1:
            self.hands = rng.choice(self.unrevealed_Cards, size=(N_OPP,INITIAL_N_CARDS-self.rounds_played), replace=False)
            self.shrinkUnrevealedCards(self.hands.flatten())

        self.board = np.zeros(shape=(4,3), dtype=np.int8) #four rows x bulls,cards,face 
        self.board[:,2] = initial_board_cards
        self.board[:,1] = 1
        self.board[:,0] = lookupTable[initial_board_cards]


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
    



    def reveal(self, cards):
        if self.game_mode == 1:
            return #Implement the heuristic selection from predetermined hands

        penalty = 0
        player_card = cards[0]
        sorted_cards = sorted(cards)
        for i in range(len(sorted_cards)):
            if sorted_cards[i] == player_card:
                penalty = self.lay(sorted_cards[i])
            else:
                self.lay(sorted_cards[i])

        self.shrinkUnrevealedCards(cards)
        #removes the card that you played from your hand
        self.my_hand.remove(player_card)
        return penalty
    
    #Some pretty bad heuristics
    def heuristicLowest(self, hand):        
        return (hand == np.min(hand)).astype(int)

    def heuristicCloseness(self, hand):
        conditions = np.zeros_like(hand)
        for i in range(len(hand)):
            if (self.board[i,2] < hand) and (self.board[i,2] + 5 > hand):
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


def main():
    game_mode = input("Gamemode:")
    gs = GameState()
    gs.__print__()
    while(gs.rounds_played != 10):
        if gs.game_mode == 0:
            cards_played = list(map(int,input("Input which cards are played:").split()))
        elif gs.game_mode == 1:
            cards_played = list(int(input("Which card did you play?:"))) #the list now only contains 1 card reveal will take care
        gs.reveal(cards=cards_played)
        gs.__print__()
        

    gs2 = copy.deepcopy(gs)
    gs2.__print__()

if __name__ == "__main__":
    main()
