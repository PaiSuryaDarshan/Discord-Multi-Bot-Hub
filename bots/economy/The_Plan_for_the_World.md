# The Plan for the World

## Project Structure

```text
bots/
└── economy/
    ├── __init__.py
    ├── bot.py                 # Loads the economy cog
    ├── cog.py                 # Slash commands
    ├── market.py              # Price simulation engine
    ├── wallet.py              # User balances
    ├── trading.py             # Buy / sell logic
    ├── rewards.py             # Math rewards, daily rewards
    ├── leaderboard.py         # Rankings
    ├── charts.py              # Price history and chart generation
    ├── events.py              # Random market events
    ├── database.py            # SQLite wrapper
    ├── utils.py               # Helpers
    ├── config.py              # Constants
    ├── tasks.py               # Background loops
    ├── views.py               # Discord buttons
    ├── embeds.py              # Embed formatting
    ├── models.py              # Dataclasses and objects
    ├── README.md
    └── data/
        ├── economy.db
        ├── market_history.json
        └── config.json

```

## Core Recommendation

The strongest version of this idea is:

A server-wide paper-trading economy where members earn currency through skill-based games, trade a simulated currency pair, and react to market events.

That is viable.

What is not viable as a first version is attempting to recreate a fully realistic financial market with order books, market makers, monetary policy, live two-second Discord charts, multiple currencies, loans, shops, taxes, and dozens of games simultaneously.

That would be technically possible but difficult to explain, balance, and maintain. Most members would ignore it.

## Recommended Economy

Use two currencies with clearly different functions:

| Currency | Purpose | Behaviour |
|---|---|---|
| Penny | Everyday currency | Earned through games and activities; relatively stable |
| Pi | Tradable asset | Limited supply; price fluctuates against Penny |

The main market becomes:

`PI/PENNY`

For example:

`1 PI = 100 PENNY`

Members earn Penny, then decide whether to:

- keep it as cash
- spend it in the server shop
- convert it into Pi
- speculate on the Pi/Penny market
- compete on a wealth leaderboard

This is much easier to understand than having three or four equally important coins.

## Market Price Model

### The Market Should Not Move Randomly for No Reason

A purely random chart becomes a gambling animation. User decisions would have almost no meaning.

Instead, price movement should contain three components:

\[
\Delta P_t
=
\underbrace{\alpha D_t}_{\text{Buying and selling pressure}}
+
\underbrace{\beta N_t}_{\text{Stochastic noise}}
+
\underbrace{\gamma E_t}_{\text{Market events}}
\]

Where:

- \(P_t\) is the current price of **Pi**, measured in **Penny**.
- \(D_t\) is the net buying/selling demand from users.
- \(N_t\) is stochastic market noise.
- \(E_t\) represents scheduled or random economic events.
- \(\alpha\), \(\beta\), and \(\gamma\) control the influence of each component on price movement.

A practical implementation could use the following return equation:

\[
r_t
=
0.003\,\tanh\!\left(\frac{B_t-S_t}{L}\right)
+
\sigma\varepsilon_t
+
e_t
\]

The market price is then updated using geometric returns:

\[
P_{t+1}
=
P_t\,e^{r_t}
\]

Where:

- \(B_t\) is the total amount of **Pi** purchased during the update interval.
- \(S_t\) is the total amount of **Pi** sold during the update interval.
- \(L\) is the market liquidity parameter.
- \(\varepsilon_t \sim \mathcal{N}(0,1)\) is Gaussian random noise.
- \(\sigma\) controls the market's volatility.
- \(e_t\) represents the impact of scheduled or random market events.

Using the hyperbolic tangent function, \(\tanh(\cdot)\), prevents extremely large trades from causing unrealistic price jumps while still allowing demand to meaningfully influence the market.

### What this achieves

- More buying generally raises the price.
- More selling generally lowers it.
- The price still moves when nobody trades.
- Major events can temporarily affect the market.
- Large users cannot completely destroy the economy with one transaction.

This does not reproduce a real financial market. It creates a defensible market simulation inspired by supply, demand and stochastic price processes. That is the accurate way to describe it publicly.

## Chart Update Frequency

### Should the Graph Update Every Two Seconds?

The internal market engine can update every two seconds.

The Discord chart should not.

Editing a Discord message or uploading a new chart every two seconds would create unnecessary API traffic and expose the bot to rate limits. Discord explicitly rate-limits API routes, including bot activity.

Use this separation:

| Component | Frequency |
|---|---|
| Internal price simulation | Every 2–5 seconds |
| Store price observation | Every 5–15 seconds |
| Generate candle | Every 1 minute |
| Update Discord market message | Every 30–60 seconds |
| Full chart command | On user request |

A Discord message might show:

```text
PI/PENNY MARKET

Price: 102.46 PENNY
1m: +0.72%
1h: -1.84%
24h High: 108.20
24h Low: 96.75

Market Status: Active
Last candle: 16:42
```

Then users run:

- `/chart`

to receive a generated line or candlestick chart.

For a genuinely smooth chart that refreshes every two seconds, build a small web dashboard and link it from Discord. Discord itself should remain the command and notification interface.

## Starting Balance

Give each new player:

- **1,000 PENNY**
- **0 PI**

Do not give them Pi immediately. Make their first Pi purchase an actual decision.

At a starting price of:

`1 PI = 100 PENNY`

a player could buy up to 10 Pi, but doing so would leave them with no liquid currency. That immediately teaches allocation.

A better onboarding structure would be:

| Item | Reward |
|---|---:|
| Starting cash | 1,000 Penny |
| First maths challenge | 100 Penny |
| Onboarding completion | 1 Pi |
| Daily claim | 20–40 Penny |
| Typical maths reward | 10–50 Penny |
| Difficult challenge | 75–150 Penny |

The single onboarding Pi introduces the asset without giving everybody a large free investment position.

## Maths Game Rewards

### Use Diminishing Rewards

Your proposed game has an obvious exploit:

People repeatedly solve easy questions and endlessly create money.

Rewards should depend on difficulty, speed and recent activity.

\[
R = R_{\text{base}} \times D \times A \times S
\]

Where:

- D is the difficulty multiplier
- A is the accuracy or streak multiplier
- S is a diminishing-return factor

Example:

| Difficulty | Base reward |
|---|---:|
| Easy | 10 Penny |
| Medium | 25 Penny |
| Hard | 50 Penny |
| Quant challenge | 100 Penny |

Then reduce repeated farming:

- Questions 1–5:    100% reward
- Questions 6–10:    75% reward
- Questions 11–20:   40% reward
- After 20:          10% reward

Reset this periodically, perhaps daily.

Otherwise the richest player will not be the best trader. It will be whoever writes a script or spends the longest answering trivial questions.

## Managing the Economy

You need both currency sources and currency sinks.

### Sources

These introduce Penny into circulation:

- maths games
- daily activity
- tournaments
- achievements
- event prizes
- moderation-approved contributions

### Sinks

These permanently remove Penny:

- trading fees
- shop purchases
- tournament entry fees
- profile customisation
- prediction-market entry
- failed challenge stakes
- cosmetic roles
- transaction taxes

Without sinks, the total Penny supply continually increases, everyone becomes nominally rich, and rewards stop feeling valuable.

A simple balance equation is:

\[
\Delta M = \text{Penny created} - \text{Penny destroyed}
\]

You should monitor:

\[
\text{Inflation Ratio}
=
\frac{\text{Penny destroyed over 7 days}}
{\text{Penny created over 7 days}}
\]

A ratio near 1 means the circulating supply is relatively stable. It does not need to be exactly 1, particularly while the server is growing.

## Essential Controls

The economy needs protections from the beginning:

- maximum trade size relative to market liquidity
- transaction fee of approximately 0.5–1%
- cooldowns on reward commands
- unique user constraints in the database
- integer or decimal-safe accounting
- no negative balances
- complete transaction ledger
- administrator adjustments recorded as transactions
- daily backups
- anti-alt-account controls
- maximum daily game earnings

Never store money using ordinary floating-point arithmetic. Use integers for Penny and a fixed precision for Pi.

For example:

```text
1 Penny = 1 internal unit
1 Pi = 1,000,000 internal micro-Pi
```

## Order Book Strategy

### Do You Need an Order Book?

Not initially.

A real order book requires:

- limit orders
- market orders
- bid and ask prices
- partial fills
- order matching
- cancelled orders
- liquidity
- spread management
- protection against manipulation

That is a substantial project by itself.

Begin with an automated market maker or simplified treasury market:

```text
/buy-pi amount:200
/sell-pi amount:1.5
```

The bot calculates the current quote, applies slippage and fees, then executes immediately.

Later, introduce:

- `/limit-buy`
- `/limit-sell`
- `/orderbook`
- `/cancel-order`

as an advanced second market.

## Keep the Commands Small

The first public version should probably have only these:

- `/balance`
- `/market`
- `/buy`
- `/sell`
- `/chart`
- `/math`
- `/leaderboard`
- `/shop`

Do not initially expose commands for monetary supply, portfolios, orders, loans, bonds, options, taxes and analytics. Complexity can exist inside the system without appearing in the basic interface.

A player should understand the loop immediately:

> **Play → Earn Penny → Buy Pi → Watch market → Sell or hold → Spend profits**

## Recommended Development Stages

### Version 1 — Functional Economy

Build:

- user wallets
- Penny rewards
- one maths game
- Pi/Penny conversion
- transaction history
- balance and leaderboard
- fixed or lightly random Pi price

This tests whether anybody cares.

### Version 2 — Simulated Market

Add:

- price engine
- stochastic noise
- buy/sell pressure
- one-minute candles
- chart generation
- transaction fees
- market events

### Version 3 — Quant Mechanics

Add:

- portfolio returns
- volatility
- moving averages
- limit orders
- market-making competition
- prediction games
- Sharpe-like leaderboard
- drawdown and risk statistics

### Version 4 — Server Economy

Only after sustained use, add:

- shops
- auctions
- player-to-player transfers
- businesses
- community projects
- loans or bonds
- additional assets

## Direct Recommendation

Build it, but frame the first version as a paper market game, not a complete simulated economy.

Use:

- one stable earning currency: Penny
- one volatile tradable asset: Pi
- a Pi/Penny market
- one-minute candles
- internal updates every five seconds
- Discord display updates every minute
- a starting balance of 1,000 Penny
- an onboarding award of 1 Pi
- diminishing maths rewards
- 0.5–1% trading fees
- no order book in the first version

The interesting complexity should come from deciding when to earn, hold, spend, buy or sell—not from forcing members to read documentation before participating.

## References

- Discord API Rate Limits
- Plotly Candlestick Charts
