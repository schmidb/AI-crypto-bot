#!/bin/bash
# Monitor next trading cycle to verify bug fixes

echo "=========================================="
echo "BUG FIX VERIFICATION MONITOR"
echo "=========================================="
echo ""
echo "Monitoring logs for next trading cycle..."
echo "Looking for:"
echo "  ✓ No timezone errors"
echo "  ✓ Capital allocation > €0"
echo "  ✓ Trade execution"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Monitor for errors and successful allocations
tail -f logs/trading_decisions.log logs/errors.log 2>/dev/null | grep --line-buffered -E "Invalid isoformat|can't compare|Allocated: €[1-9]|executed|PRIORITIZED|Error"
