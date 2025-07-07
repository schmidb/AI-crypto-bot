// Multi-Strategy Dashboard JavaScript

// Update multi-strategy display for each asset
function updateMultiStrategyDisplay(asset, decisionData) {
    const assetCard = document.querySelector(`[data-asset="${asset}"]`);
    if (!assetCard) return;
    
    const strategyDetails = decisionData.strategy_details || {};
    
    // Update market regime
    const regimeBadge = assetCard.querySelector('.market-regime-badge');
    if (regimeBadge) {
        const regime = strategyDetails.market_regime || 'unknown';
        regimeBadge.textContent = regime.toUpperCase();
        regimeBadge.className = `market-regime-badge badge bg-info ${regime}`;
    }
    
    // Update combined signal
    const combinedSignal = strategyDetails.combined_signal || {};
    updateCombinedSignal(assetCard, combinedSignal);
    
    // Update individual strategies
    const individualStrategies = strategyDetails.individual_strategies || {};
    updateIndividualStrategies(assetCard, individualStrategies);
}

function updateCombinedSignal(assetCard, combinedSignal) {
    const actionBadge = assetCard.querySelector('.combined-action-badge');
    const confidenceFill = assetCard.querySelector('.confidence-fill');
    const confidenceText = assetCard.querySelector('.confidence-text');
    
    if (actionBadge) {
        const action = combinedSignal.action || 'HOLD';
        actionBadge.textContent = action;
        actionBadge.className = `combined-action-badge badge ${action}`;
    }
    
    if (confidenceFill && confidenceText) {
        const confidence = combinedSignal.confidence || 0;
        confidenceFill.style.width = `${confidence}%`;
        confidenceText.textContent = `${confidence.toFixed(1)}%`;
    }
}

function updateIndividualStrategies(assetCard, individualStrategies) {
    const strategySignals = assetCard.querySelector('.strategy-signals');
    if (!strategySignals) return;
    
    const strategies = ['trend_following', 'mean_reversion', 'momentum'];
    const strategyNames = {
        'trend_following': 'Trend Following',
        'mean_reversion': 'Mean Reversion',
        'momentum': 'Momentum'
    };
    
    strategies.forEach(strategyKey => {
        const strategyData = individualStrategies[strategyKey];
        const strategyElement = strategySignals.querySelector(`[data-strategy="${strategyKey}"]`);
        
        if (strategyElement && strategyData) {
            const actionBadge = strategyElement.querySelector('.strategy-action');
            const confidenceSpan = strategyElement.querySelector('.strategy-confidence');
            
            if (actionBadge) {
                const action = strategyData.action || 'HOLD';
                actionBadge.textContent = action;
                actionBadge.className = `strategy-action badge ${action}`;
            }
            
            if (confidenceSpan) {
                const confidence = strategyData.confidence || 0;
                confidenceSpan.textContent = `${confidence.toFixed(1)}%`;
            }
        }
    });
}

// Handle expand/collapse for strategy details
function initializeStrategyExpansion() {
    document.addEventListener('click', function(e) {
        if (e.target.closest('.expand-strategies')) {
            const button = e.target.closest('.expand-strategies');
            const strategiesSection = button.closest('.multi-strategy-section').querySelector('.individual-strategies');
            const icon = button.querySelector('i');
            
            if (strategiesSection.style.display === 'none' || !strategiesSection.style.display) {
                strategiesSection.style.display = 'block';
                button.innerHTML = '<i class="fas fa-chevron-up me-1"></i>Hide Strategy Details';
                button.classList.add('expanded');
            } else {
                strategiesSection.style.display = 'none';
                button.innerHTML = '<i class="fas fa-chevron-down me-1"></i>Show Strategy Details';
                button.classList.remove('expanded');
            }
        }
    });
}

// Initialize multi-strategy functionality
function initializeMultiStrategy() {
    initializeStrategyExpansion();
    
    // Add data attributes to asset cards for easier targeting
    const assetCards = document.querySelectorAll('.market-asset-card');
    assetCards.forEach((card, index) => {
        const assets = ['BTC', 'ETH', 'SOL'];
        if (index < assets.length) {
            card.setAttribute('data-asset', assets[index]);
        }
    });
}

// Update strategy weights display (if needed)
function updateStrategyWeights(weights) {
    // This could be used to show strategy weights in a separate section
    console.log('Strategy weights:', weights);
}

// Export functions for use in main dashboard
window.MultiStrategy = {
    updateDisplay: updateMultiStrategyDisplay,
    initialize: initializeMultiStrategy,
    updateWeights: updateStrategyWeights
};
