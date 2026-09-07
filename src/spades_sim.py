import random
import matplotlib.pyplot as plt
import numpy as np
import math

num_trials = 10000

## general setup
# 52 card deck
suits = ['Spades', 'Hearts', 'Diamonds', 'Clubs']
ranks = range(2,15) # 2-10 numbered + face cards
#define deck
deck = [(rank, suit) for suit in suits for rank in ranks]

#shuffle deck and randomly deal your hand
#random for this instance, otherwise would input actual dealt hand
random.shuffle(deck)
my_hand = deck[:13]
#my_hand = [(13, 'Clubs'), (7, 'Diamonds'), (11, 'Spades'), (5, 'Diamonds'), (14, 'Diamonds'), (6, 'Spades'), (9, 'Spades'), (2, 'Hearts'), (13, 'Spades'), (14, 'Spades'), (6, 'Diamonds'), (5, 'Spades'), (5, 'Hearts')]
#for card in my_hand:
#    deck.remove(card)
#assign remaining cards
remaining_cards = deck[13:]

#determine which cards are legally playable
def legal_cards(hand, trick, spades_broken):
    if trick:
        led_suit = trick[0][1][1]
        cards_in_suit = [
            card for card in hand if card[1] == led_suit
        ]

        #if following, have to play card of same suit if possible
        if cards_in_suit:
            return cards_in_suit

        #if no cards of led suit, can play any card
        return hand

    #can't lead with spades until they are broken
    if not spades_broken:
        not_spades = [
            card for card in hand
            if card[1] != 'Spades'
        ]

        #returns cards that arent spades, if there are any
        if not_spades:
            return not_spades

    #if leading and spades are broken, any card is legal
    return hand


# determine if any given card in hand can beat current winning card
def beats(card, winning_card, led_suit):
    if winning_card is None:
        return True

    winner_rank, winner_suit = winning_card

    #spades always trump
    #if candidate card is spades and winning card is not, candidate wins
    if card[1] == 'Spades' and winner_suit != 'Spades':
        return True

    #opposite is true as well
    if card[1] != 'Spades' and winner_suit == 'Spades':
        return False

    #cards that do not follow suit cannot win
    if card[1] != winner_suit:
        return False

    #otherwise, just check the rank of each card
    return card[0] > winner_rank


## choose a card to play from the legal cards
#continue working here !!
def play_card(hand, trick, spades_broken):
    choices= legal_cards(hand, trick, spades_broken)

    #lead largest legal card (change)
    if not trick:
        return max(choices, key=lambda card: card[0])
        #note to self b/c I still don't understand
        #min takes two arguments, the iterable and the key function.
        #lambda represents a temporary function that takes a card as input and returns its rank (card[0]).
        # ie. key = lambda card (#card is the input) : card[0] (#the output, item 0 of the card's ordered pair, which is the rank)

    led_suit = trick[0][1][1]
    current_winner = trick[0][1]

    winning_options = [
        card for card in choices
        if beats(card, current_winner, led_suit)
    ]

    if winning_options:
        return min(winning_options, key=lambda card: card[0])
        #cheapest way to win

    non_spades = [
        card for card in choices
        if card[1] != 'Spades'
    ]

    return min(non_spades or choices, key=lambda card: card[0])


#card playing logic when trying to bid zero

def play_card_nil(hand, trick, spades_broken):
    choices = legal_cards(hand, trick, spades_broken)

    #lead smallest card
    if not trick:
        return min(choices, key=lambda card: card[0])
        # "if not trick" means if trick is empty, which it is when
        # no one has played a card, then you are leading

    led_suit = trick[0][1][1]
    current_winner = trick[0][1]

    safe = [c for c in choices if not beats(c, current_winner, led_suit)]

    #dumpest highest safe card possible
    if safe:
        return max(safe, key=lambda c: c[0])
    
    #forced to win, take cheapest win
    return min(choices, key=lambda c: c[0])

    


#play single trick
def play_trick(hands, start_player, spades_broken):
    trick = []
    player_order = [
        (start_player + i) % 4 for i in range(4)
    ]

    for player in player_order:
        # player plays card, removed from hand, added to trick
        card = play_card(hands[player], trick, spades_broken)
        hands[player].remove(card)
        trick.append((player, card))

        if card[1] == 'Spades':
            spades_broken = True

    led_suit = trick[0][1][1]
    winning_player, winning_card = trick[0]
    # starting player is winning initially
    # has to be updated as each player plays a card

    for player, card in trick[1:]:
        if beats(card, winning_card, led_suit):
            winning_player = player
            winning_card = card

    #return the winning player
    return winning_player, spades_broken


#play a full game of 13 tricks
def play_game(my_hand, cards_left):
    shuffled_cards = cards_left.copy()
    random.shuffle(shuffled_cards)

    # define every player's hand
    # player 0 is the user

    hands = [
        my_hand.copy(),
        shuffled_cards[0:13],
        shuffled_cards[13:26],
        shuffled_cards[26:39]
    ]

    tricks_won = [0, 0, 0, 0] # each player starts with no tricks taken
    start_player = 0
    spades_broken = False

    #13 tricks
    for trick_num in range(13):
        winner, spades_broken = play_trick(
            hands,
            start_player,
            spades_broken
        )
        tricks_won[winner] += 1
        start_player = winner

    #return number of tricks won by player 0 (user)
    return tricks_won[0]

def est_tricks(my_hand, num_trials):
    remaining_cards = [
        card for card in deck
        if card not in my_hand
    ]

    #start with no tricks, obviously
    total_tricks = 0

    for i in range(num_trials):
        total_tricks += play_game(
            my_hand,
            remaining_cards
        )

    return total_tricks / num_trials


'''
not sure what I was doing here tbh. 
the next section of plotting is more accurate?
'''
#reminder that for running multiple games, starting player should rotate. starting with p0, for instance, and then p1, p2, etc

#final_estimation = est_tricks(my_hand, num_trials)
#print("hand:", my_hand)
#print("estimated tricks taken:", final_estimation)

#plt.figure(figsize=(10,6))
#plt.plot(range(num_trials), [est_tricks(my_hand, i+1) for i in range(num_trials)])

#x= np.linspace(0, num_trials, num_trials)
#y = [final_estimation]
#plt.plot(x,y, color='red', label = 'y='+str(final_estimation))
#plt.axhline(y=final_estimation, color='red', label='y='+str(final_estimation))





results = np.array([play_game(my_hand, remaining_cards) for i in range(num_trials)])
running_mean = np.cumsum(results) / np.arange(1, num_trials + 1)

print("Hand:", my_hand)
print("Estimated Tricks Taken:", results.mean())
#print("Tricks Taken on Random Trial:",results[random.randint(0, num_trials-1)])

#plotting convergence of sim towards mean tricks taken for given hand
'''
plt.plot(running_mean)
plt.axhline(results.mean(), color='red', label='y='+str(results.mean()))

plt.xlabel("Number of Trials")
plt.ylabel("Estimated Tricks Taken")
plt.title("Convergence of Monte Carlo Simulation")
plt.show()
'''

'''
implementing bidding logic
'''

#possible bids
b = range(0,14)
per_bid_scores = []
#1-13 possible bids
#logic for bidding zero is different

def score_bids(trial_results=None):
    """Return the average score for each possible bid."""
    if trial_results is None:
        trial_results = results

    trial_count = len(trial_results)
    if trial_count == 0:
        raise ValueError("trial_results must contain at least one result")

    bid_scores = []
    for bid in b:
        total_score = 0
        for tricks_taken in trial_results:
            if bid == 0:
                score = 100 if tricks_taken == 0 else -100
            elif tricks_taken >= bid:
                score = 10 * bid + (tricks_taken - bid)
            else:
                score = -10 * bid

            total_score += score

        bid_scores.append(math.floor(total_score / trial_count))

    return bid_scores

per_bid_scores = score_bids()
print("List of average scores for each bid:", per_bid_scores)
highest_score = max(per_bid_scores)
best_bid = per_bid_scores.index(highest_score)

print("Recommended Bid of", best_bid, "with an average score of", highest_score)
print("Score breakdown. Points for bid:", 10*(best_bid), ". Points for overtricks:", highest_score - 10*(best_bid))

'''
to implement:
- actively trying to bid zero if dealt poor hand
- bag penalty and logic trying to avoid bags
- not taking tricks from partners (players 0 and 2, players 1 and 3)
'''



