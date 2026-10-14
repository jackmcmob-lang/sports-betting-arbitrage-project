import requests

BOOKMAKER_INDEX = 0
NAME_INDEX = 1
ODDS_INDEX = 2
FIRST = 0


class Event:
    def __init__(self, data):
        self.data = data
        self.sport_key = data['sport_key']
        self.sport_title = data.get('sport_title', data['sport_key'])
        self.home_team = data.get('home_team')
        self.away_team = data.get('away_team')
        self.commence_time = data.get('commence_time')
        self.id = data['id']

    def find_best_odds(self):
        # some events have no bookmaker odds posted yet for this market/region
        if not self.data['bookmakers'] or not self.data['bookmakers'][FIRST]['markets']:
            self.num_outcomes = 0
            self.best_odds = []
            return []

        num_outcomes = len(self.data['bookmakers'][FIRST]['markets'][FIRST]['outcomes'])
        self.num_outcomes = num_outcomes

        best_odds = [[None, None, float('-inf')] for _ in range(num_outcomes)]

        bookmakers = self.data['bookmakers']
        for bookmaker in bookmakers:
            for outcome in range(num_outcomes):
                bookmaker_odds = float(bookmaker['markets'][FIRST]['outcomes'][outcome]['price'])
                current_best_odds = best_odds[outcome][ODDS_INDEX]

                if bookmaker_odds > current_best_odds:
                    best_odds[outcome][BOOKMAKER_INDEX] = bookmaker['title']
                    best_odds[outcome][NAME_INDEX] = bookmaker['markets'][FIRST]['outcomes'][outcome]['name']
                    best_odds[outcome][ODDS_INDEX] = bookmaker_odds

        self.best_odds = best_odds
        return best_odds

    def arbitrage(self, bet_size):
        total_arbitrage_percentage = 0
        for odds in self.best_odds:
            total_arbitrage_percentage += (1.0 / odds[ODDS_INDEX])

        self.total_arbitrage_percentage = total_arbitrage_percentage
        self.expected_earnings = (bet_size / total_arbitrage_percentage) - bet_size

        return total_arbitrage_percentage < 1

    def calculate_arbitrage_bets(self, bet_size):
        bet_amounts = []
        for outcome in range(self.num_outcomes):
            individual_arbitrage_percentage = 1 / self.best_odds[outcome][ODDS_INDEX]
            bet_amount = (bet_size * individual_arbitrage_percentage) / self.total_arbitrage_percentage
            bet_amounts.append(round(bet_amount, 2))

        self.bet_amounts = bet_amounts
        return bet_amounts


def fetch_odds_response(api_key, sport='upcoming', regions='us', markets='h2h',
                         odds_format='decimal', date_format='iso'):
    odds_response = requests.get(
        f'https://api.the-odds-api.com/v4/sports/{sport}/odds',
        params={
            'api_key': api_key,
            'regions': regions,
            'markets': markets,
            'oddsFormat': odds_format,
            'dateFormat': date_format,
        },
    ).json()

    if not isinstance(odds_response, list):
        raise RuntimeError(f'Unexpected response from The Odds API: {odds_response}')

    return odds_response


def find_arbitrage_events(odds_response, bet_size=100):
    arbitrage_events = []
    for data in odds_response:
        event = Event(data)
        best_odds = event.find_best_odds()
        if not best_odds:
            continue
        if event.arbitrage(bet_size):
            event.calculate_arbitrage_bets(bet_size)
            arbitrage_events.append(event)

    return arbitrage_events
