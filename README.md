## Portfolio-Based Trading Strategy

The bot implements a sophisticated portfolio-based trading strategy that allows you to start with existing cryptocurrency holdings rather than USD.

### How It Works

1. **Initial Portfolio Setup**:
   - You specify your initial BTC and ETH amounts in the configuration
   - The bot tracks your portfolio value and performance over time
   - All holdings and trades are stored in a persistent portfolio file

2. **Dynamic Trade Sizing**:
   - Trade sizes are proportional to the AI's confidence level
   - Higher confidence leads to larger position sizes
   - The MAX_TRADE_PERCENTAGE setting limits how much of your holdings can be traded at once

3. **Portfolio Rebalancing**:
   - The bot can automatically maintain your target asset allocation (e.g., 40% BTC, 40% ETH, 20% USD)
   - Rebalancing occurs when allocations drift beyond a configurable threshold
   - This ensures your portfolio stays aligned with your investment strategy

4. **Performance Tracking**:
   - The bot tracks your portfolio's total value in USD
   - Performance is measured against your initial holdings
   - Detailed trade history and performance metrics are logged

### Configuration

Configure your portfolio strategy in the `.env` file:

```
# Portfolio settings
INITIAL_BTC_AMOUNT=0.01       # Your starting BTC amount
INITIAL_ETH_AMOUNT=0.15       # Your starting ETH amount
PORTFOLIO_REBALANCE=true      # Enable automatic portfolio rebalancing
MAX_TRADE_PERCENTAGE=25       # Maximum percentage of holdings to trade at once
```

### Benefits

- **Start with existing crypto**: No need to convert to USD first
- **Efficient capital use**: Reinvests proceeds from sales into new opportunities
- **Risk management**: Limits exposure through percentage-based position sizing
- **Automated rebalancing**: Maintains your desired asset allocation
- **Performance tracking**: Monitors your portfolio's growth over time
