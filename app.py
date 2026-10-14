import os

from flask import Flask, render_template, request

from arbitrage import fetch_odds_response, find_arbitrage_events

app = Flask(__name__)


def get_api_key():
    env_key = os.environ.get('ODDS_API_KEY')
    if env_key:
        return env_key.strip()

    for filename in ('API_KEY.local.txt', 'API_KEY.txt'):
        if os.path.exists(filename):
            with open(filename) as f:
                key = f.read().strip()
            if key and key != 'PLACE API KEY HERE':
                return key

    return None


@app.route('/')
def index():
    bet_size = request.args.get('bet_size', default=100, type=float)
    api_key = get_api_key()

    if not api_key:
        return render_template(
            'index.html',
            error="No API key found. Put your real key in API_KEY.local.txt or set the ODDS_API_KEY environment variable.",
            events=None,
            bet_size=bet_size,
        )

    try:
        odds_response = fetch_odds_response(api_key)
        events = find_arbitrage_events(odds_response, bet_size=bet_size)
    except Exception as exc:
        return render_template('index.html', error=str(exc), events=None, bet_size=bet_size)

    return render_template('index.html', error=None, events=events, bet_size=bet_size)


if __name__ == '__main__':
    app.run(debug=True)
