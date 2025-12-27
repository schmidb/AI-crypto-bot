# Performance Analysis

The AI crypto trading bot includes comprehensive performance tracking and analysis capabilities to monitor trading effectiveness, risk management, and system health.

## Performance Tracking System

### Real-Time Monitoring

#### Portfolio Snapshots
The system takes regular snapshots of portfolio state:

```python
class PerformanceTracker:
    def take_portfolio_snapshot(self, portfolio, market_data):
        snapshot = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_value_eur': portfolio.calculate_total_value(),
            'assets': {
                asset: {
                    'amount': data['amount'],
                    'value_eur': data['amount'] * market_data[asset]['price'],
                    'allocation_percent': allocation
                }
                for asset, data in portfolio.assets.items()
            },
            'cash_eur': portfolio.cash,
            'market_prices': {
                asset: market_data[asset]['price'] 
                for asset in portfolio.assets.keys()
            }
        }
        
        self.snapshots.append(snapshot)
        self.save_snapshot(snapshot)
```

#### Snapshot Frequency
- **Hourly**: During active trading periods
- **Daily**: Minimum snapshot frequency
- **Trade-Triggered**: After each trade execution
- **Event-Driven**: Market volatility spikes, system restarts

### Performance Metrics

#### Return Calculations

```python
class PerformanceCalculator:
    def calculate_returns(self, snapshots, period='all'):
        if len(snapshots) < 2:
            return None
            
        # Filter snapshots by period
        filtered_snapshots = self.filter_by_period(snapshots, period)
        
        start_value = filtered_snapshots[0]['total_value_eur']
        end_value = filtered_snapshots[-1]['total_value_eur']
        
        # Total return
        total_return = (end_value - start_value) / start_value
        
        # Time-weighted return
        days = (
            datetime.fromisoformat(filtered_snapshots[-1]['timestamp']) -
            datetime.fromisoformat(filtered_snapshots[0]['timestamp'])
        ).days
        
        # Annualized return
        if days > 0:
            annualized_return = (end_value / start_value) ** (365 / days) - 1
        else:
            annualized_return = 0
            
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'period_days': days,
            'start_value': start_value,
            'end_value': end_value
        }
```

#### Risk Metrics

```python
def calculate_risk_metrics(self, snapshots):
    # Calculate daily returns
    daily_returns = []
    for i in range(1, len(snapshots)):
        prev_value = snapshots[i-1]['total_value_eur']
        curr_value = snapshots[i]['total_value_eur']
        daily_return = (curr_value - prev_value) / prev_value
        daily_returns.append(daily_return)
    
    if not daily_returns:
        return None
    
    returns_array = np.array(daily_returns)
    
    # Volatility (annualized)
    volatility = np.std(returns_array) * np.sqrt(365)
    
    # Sharpe Ratio (assuming 2% risk-free rate)
    risk_free_rate = 0.02
    mean_return = np.mean(returns_array) * 365
    sharpe_ratio = (mean_return - risk_free_rate) / volatility if volatility > 0 else 0
    
    # Maximum Drawdown
    cumulative_values = [s['total_value_eur'] for s in snapshots]
    running_max = np.maximum.accumulate(cumulative_values)
    drawdowns = (np.array(cumulative_values) - running_max) / running_max
    max_drawdown = np.min(drawdowns)
    
    # Sortino Ratio (downside deviation)
    downside_returns = returns_array[returns_array < 0]
    if len(downside_returns) > 0:
        downside_deviation = np.std(downside_returns) * np.sqrt(365)
        sortino_ratio = (mean_return - risk_free_rate) / downside_deviation
    else:
        sortino_ratio = float('inf')
    
    return {
        'volatility': volatility,
        'sharpe_ratio': sharpe_ratio,
        'sortino_ratio': sortino_ratio,
        'max_drawdown': max_drawdown,
        'downside_deviation': downside_deviation if len(downside_returns) > 0 else 0
    }
```

### Trading Performance Analysis

#### Trade-Level Metrics

```python
def analyze_trading_performance(self, trades, period=None):
    if period:
        trades = self.filter_trades_by_period(trades, period)
    
    if not trades:
        return None
    
    # Separate winning and losing trades
    winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
    losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
    
    # Basic statistics
    total_trades = len(trades)
    winning_trades_count = len(winning_trades)
    losing_trades_count = len(losing_trades)
    
    # Win rate
    win_rate = winning_trades_count / total_trades if total_trades > 0 else 0
    
    # Average win/loss
    avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
    avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
    
    # Profit factor
    total_wins = sum(t['pnl'] for t in winning_trades)
    total_losses = abs(sum(t['pnl'] for t in losing_trades))
    profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
    
    # Expectancy
    expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
    
    return {
        'total_trades': total_trades,
        'winning_trades': winning_trades_count,
        'losing_trades': losing_trades_count,
        'win_rate': win_rate,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'profit_factor': profit_factor,
        'expectancy': expectancy,
        'total_pnl': sum(t.get('pnl', 0) for t in trades)
    }
```

## Performance Dashboard

### Real-Time Metrics Display

#### Portfolio Overview
```html
<!-- Dashboard snippet -->
<div class="portfolio-overview">
    <div class="metric-card">
        <h3>Total Portfolio Value</h3>
        <span class="value">€{{ portfolio.total_value | number:2 }}</span>
        <span class="change {{ portfolio.daily_change >= 0 ? 'positive' : 'negative' }}">
            {{ portfolio.daily_change | percentage:2 }}
        </span>
    </div>
    
    <div class="metric-card">
        <h3>24h Performance</h3>
        <span class="value">{{ performance.daily_return | percentage:2 }}</span>
        <span class="trades">{{ performance.trades_today }} trades</span>
    </div>
    
    <div class="metric-card">
        <h3>Total Return</h3>
        <span class="value">{{ performance.total_return | percentage:2 }}</span>
        <span class="period">Since {{ performance.start_date | date }}</span>
    </div>
</div>
```

#### Performance Charts
```javascript
// Performance chart configuration
const performanceChart = {
    type: 'line',
    data: {
        labels: timestamps,
        datasets: [{
            label: 'Portfolio Value',
            data: portfolioValues,
            borderColor: '#4CAF50',
            backgroundColor: 'rgba(76, 175, 80, 0.1)',
            fill: true
        }, {
            label: 'BTC Benchmark',
            data: benchmarkValues,
            borderColor: '#FF9800',
            backgroundColor: 'transparent',
            borderDash: [5, 5]
        }]
    },
    options: {
        responsive: true,
        scales: {
            y: {
                beginAtZero: false,
                ticks: {
                    callback: function(value) {
                        return '€' + value.toFixed(2);
                    }
                }
            }
        },
        plugins: {
            tooltip: {
                callbacks: {
                    label: function(context) {
                        return context.dataset.label + ': €' + context.parsed.y.toFixed(2);
                    }
                }
            }
        }
    }
};
```

### Performance Reports

#### Daily Performance Summary
```python
def generate_daily_summary(self):
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    # Get today's snapshots
    today_snapshots = self.get_snapshots_for_date(today)
    yesterday_snapshots = self.get_snapshots_for_date(yesterday)
    
    if not today_snapshots or not yesterday_snapshots:
        return None
    
    # Calculate daily performance
    start_value = yesterday_snapshots[-1]['total_value_eur']
    end_value = today_snapshots[-1]['total_value_eur']
    daily_return = (end_value - start_value) / start_value
    
    # Get today's trades
    today_trades = self.get_trades_for_date(today)
    
    # Trading activity
    buy_trades = [t for t in today_trades if t['action'] == 'BUY']
    sell_trades = [t for t in today_trades if t['action'] == 'SELL']
    
    return {
        'date': today.isoformat(),
        'start_value': start_value,
        'end_value': end_value,
        'daily_return': daily_return,
        'daily_pnl': end_value - start_value,
        'trades_executed': len(today_trades),
        'buy_trades': len(buy_trades),
        'sell_trades': len(sell_trades),
        'trading_volume': sum(t.get('amount', 0) for t in today_trades),
        'assets_allocation': self.calculate_current_allocation()
    }
```

#### Weekly/Monthly Reports
```python
def generate_period_report(self, period='week'):
    end_date = datetime.now().date()
    
    if period == 'week':
        start_date = end_date - timedelta(days=7)
    elif period == 'month':
        start_date = end_date - timedelta(days=30)
    else:
        raise ValueError("Period must be 'week' or 'month'")
    
    # Get period snapshots
    snapshots = self.get_snapshots_for_period(start_date, end_date)
    trades = self.get_trades_for_period(start_date, end_date)
    
    # Calculate performance metrics
    returns = self.calculate_returns(snapshots)
    risk_metrics = self.calculate_risk_metrics(snapshots)
    trading_performance = self.analyze_trading_performance(trades)
    
    # Strategy performance breakdown
    strategy_performance = self.analyze_strategy_performance(trades)
    
    return {
        'period': period,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'returns': returns,
        'risk_metrics': risk_metrics,
        'trading_performance': trading_performance,
        'strategy_performance': strategy_performance,
        'market_conditions': self.analyze_market_conditions(start_date, end_date)
    }
```

## Strategy Performance Analysis

### Individual Strategy Tracking

```python
def analyze_strategy_performance(self, trades):
    strategy_stats = {}
    
    for trade in trades:
        strategy = trade.get('strategy', 'unknown')
        
        if strategy not in strategy_stats:
            strategy_stats[strategy] = {
                'trades': [],
                'total_pnl': 0,
                'winning_trades': 0,
                'losing_trades': 0
            }
        
        strategy_stats[strategy]['trades'].append(trade)
        strategy_stats[strategy]['total_pnl'] += trade.get('pnl', 0)
        
        if trade.get('pnl', 0) > 0:
            strategy_stats[strategy]['winning_trades'] += 1
        elif trade.get('pnl', 0) < 0:
            strategy_stats[strategy]['losing_trades'] += 1
    
    # Calculate metrics for each strategy
    for strategy, stats in strategy_stats.items():
        total_trades = len(stats['trades'])
        win_rate = stats['winning_trades'] / total_trades if total_trades > 0 else 0
        
        strategy_stats[strategy].update({
            'total_trades': total_trades,
            'win_rate': win_rate,
            'avg_pnl_per_trade': stats['total_pnl'] / total_trades if total_trades > 0 else 0,
            'contribution_to_total': stats['total_pnl']
        })
    
    return strategy_stats
```

### Market Regime Performance

```python
def analyze_market_regime_performance(self, start_date, end_date):
    # Get market data for period
    market_data = self.get_market_data_for_period(start_date, end_date)
    trades = self.get_trades_for_period(start_date, end_date)
    
    # Classify market regimes
    regimes = self.classify_market_regimes(market_data)
    
    # Group trades by market regime
    regime_performance = {}
    
    for trade in trades:
        trade_date = datetime.fromisoformat(trade['timestamp']).date()
        regime = self.get_regime_for_date(regimes, trade_date)
        
        if regime not in regime_performance:
            regime_performance[regime] = {
                'trades': [],
                'total_pnl': 0,
                'days': 0
            }
        
        regime_performance[regime]['trades'].append(trade)
        regime_performance[regime]['total_pnl'] += trade.get('pnl', 0)
    
    # Calculate regime-specific metrics
    for regime, stats in regime_performance.items():
        regime_days = sum(1 for r in regimes if r['regime'] == regime)
        stats['days'] = regime_days
        stats['trades_per_day'] = len(stats['trades']) / regime_days if regime_days > 0 else 0
        stats['pnl_per_day'] = stats['total_pnl'] / regime_days if regime_days > 0 else 0
    
    return regime_performance
```

## Benchmarking

### Benchmark Comparison

```python
def compare_to_benchmark(self, benchmark_symbol='BTC-EUR'):
    # Get portfolio performance
    portfolio_snapshots = self.get_all_snapshots()
    portfolio_returns = self.calculate_returns(portfolio_snapshots)
    
    # Get benchmark data
    benchmark_data = self.get_benchmark_data(benchmark_symbol)
    benchmark_returns = self.calculate_benchmark_returns(benchmark_data)
    
    # Calculate relative performance
    alpha = portfolio_returns['annualized_return'] - benchmark_returns['annualized_return']
    
    # Calculate beta (portfolio sensitivity to benchmark)
    portfolio_daily_returns = self.get_daily_returns(portfolio_snapshots)
    benchmark_daily_returns = self.get_daily_returns(benchmark_data)
    
    covariance = np.cov(portfolio_daily_returns, benchmark_daily_returns)[0][1]
    benchmark_variance = np.var(benchmark_daily_returns)
    beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
    
    # Information ratio
    tracking_error = np.std(np.array(portfolio_daily_returns) - np.array(benchmark_daily_returns)) * np.sqrt(365)
    information_ratio = alpha / tracking_error if tracking_error > 0 else 0
    
    return {
        'portfolio_return': portfolio_returns['annualized_return'],
        'benchmark_return': benchmark_returns['annualized_return'],
        'alpha': alpha,
        'beta': beta,
        'information_ratio': information_ratio,
        'tracking_error': tracking_error
    }
```

## Performance Optimization

### Automated Performance Analysis

```python
class PerformanceOptimizer:
    def analyze_underperformance(self, threshold_days=7):
        """Identify periods of underperformance and suggest improvements"""
        
        recent_performance = self.get_recent_performance(threshold_days)
        
        if recent_performance['daily_return'] < -0.02:  # -2% threshold
            analysis = {
                'issue': 'underperformance',
                'severity': 'high' if recent_performance['daily_return'] < -0.05 else 'medium',
                'recommendations': []
            }
            
            # Analyze potential causes
            if recent_performance['volatility'] > 0.4:
                analysis['recommendations'].append('Reduce position sizes due to high volatility')
            
            if recent_performance['win_rate'] < 0.4:
                analysis['recommendations'].append('Review strategy parameters - low win rate')
            
            if recent_performance['max_drawdown'] < -0.1:
                analysis['recommendations'].append('Implement stricter stop-loss mechanisms')
            
            return analysis
        
        return None
    
    def suggest_strategy_adjustments(self):
        """Suggest strategy weight adjustments based on recent performance"""
        
        strategy_performance = self.analyze_strategy_performance_last_30_days()
        current_weights = self.get_current_strategy_weights()
        
        suggestions = {}
        
        for strategy, performance in strategy_performance.items():
            current_weight = current_weights.get(strategy, 0)
            
            if performance['sharpe_ratio'] > 1.5 and current_weight < 0.5:
                suggestions[strategy] = {
                    'action': 'increase_weight',
                    'current_weight': current_weight,
                    'suggested_weight': min(current_weight + 0.1, 0.5),
                    'reason': f'High Sharpe ratio: {performance["sharpe_ratio"]:.2f}'
                }
            elif performance['sharpe_ratio'] < 0.5 and current_weight > 0.2:
                suggestions[strategy] = {
                    'action': 'decrease_weight',
                    'current_weight': current_weight,
                    'suggested_weight': max(current_weight - 0.1, 0.2),
                    'reason': f'Low Sharpe ratio: {performance["sharpe_ratio"]:.2f}'
                }
        
        return suggestions
```

## Performance Alerts

### Automated Monitoring

```python
class PerformanceAlerts:
    def __init__(self, config):
        self.config = config
        self.alert_thresholds = {
            'daily_loss_threshold': -0.05,  # -5%
            'drawdown_threshold': -0.15,    # -15%
            'volatility_threshold': 0.5,    # 50%
            'win_rate_threshold': 0.3       # 30%
        }
    
    def check_performance_alerts(self):
        alerts = []
        
        # Daily performance check
        daily_performance = self.get_daily_performance()
        if daily_performance['return'] < self.alert_thresholds['daily_loss_threshold']:
            alerts.append({
                'type': 'daily_loss',
                'severity': 'high',
                'message': f"Daily loss of {daily_performance['return']:.2%} exceeds threshold",
                'value': daily_performance['return'],
                'threshold': self.alert_thresholds['daily_loss_threshold']
            })
        
        # Drawdown check
        current_drawdown = self.get_current_drawdown()
        if current_drawdown < self.alert_thresholds['drawdown_threshold']:
            alerts.append({
                'type': 'max_drawdown',
                'severity': 'critical',
                'message': f"Drawdown of {current_drawdown:.2%} exceeds threshold",
                'value': current_drawdown,
                'threshold': self.alert_thresholds['drawdown_threshold']
            })
        
        # Win rate check (last 20 trades)
        recent_win_rate = self.get_recent_win_rate(20)
        if recent_win_rate < self.alert_thresholds['win_rate_threshold']:
            alerts.append({
                'type': 'low_win_rate',
                'severity': 'medium',
                'message': f"Win rate of {recent_win_rate:.2%} below threshold",
                'value': recent_win_rate,
                'threshold': self.alert_thresholds['win_rate_threshold']
            })
        
        return alerts
    
    def send_alerts(self, alerts):
        for alert in alerts:
            if alert['severity'] == 'critical':
                self.send_immediate_notification(alert)
            else:
                self.queue_daily_report_alert(alert)
```

## Configuration

### Performance Tracking Settings

```env
# Performance tracking configuration
PERFORMANCE_TRACKING_ENABLED=true
SNAPSHOT_FREQUENCY_MINUTES=60
PERFORMANCE_RETENTION_DAYS=365
BENCHMARK_SYMBOL=BTC-EUR

# Alert thresholds
DAILY_LOSS_ALERT_THRESHOLD=-0.05
MAX_DRAWDOWN_ALERT_THRESHOLD=-0.15
WIN_RATE_ALERT_THRESHOLD=0.30
VOLATILITY_ALERT_THRESHOLD=0.50

# Reporting
DAILY_REPORT_ENABLED=true
WEEKLY_REPORT_ENABLED=true
PERFORMANCE_DASHBOARD_ENABLED=true
```

This comprehensive performance analysis system provides deep insights into trading effectiveness, enabling continuous optimization and risk management of the AI crypto trading bot.