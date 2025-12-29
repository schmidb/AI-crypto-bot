#!/bin/bash
"""
Check Google VM Status and Costs

This script shows your current VM configuration, status, and estimated costs.
"""

set -e  # Exit on any error

# Configuration - UPDATE THESE VALUES
VM_NAME="${VM_NAME:-aicryptobot}"
ZONE="${ZONE:-us-central1-a}"
PROJECT="${PROJECT:-intense-base-456414-u5}"

echo "📊 VM Status and Cost Information"
echo "================================="
echo "VM Name: $VM_NAME"
echo "Zone: $ZONE"
echo "Project: $PROJECT"
echo ""

# Check if VM exists
if ! gcloud compute instances describe $VM_NAME --zone=$ZONE --project=$PROJECT >/dev/null 2>&1; then
    echo "❌ VM '$VM_NAME' not found in zone '$ZONE'"
    echo "Please check your VM name and zone settings."
    exit 1
fi

# Get VM details
VM_INFO=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --project=$PROJECT --format="json")

STATUS=$(echo "$VM_INFO" | jq -r '.status')
MACHINE_TYPE=$(echo "$VM_INFO" | jq -r '.machineType' | sed 's|.*/||')
ZONE_FULL=$(echo "$VM_INFO" | jq -r '.zone' | sed 's|.*/||')
EXTERNAL_IP=$(echo "$VM_INFO" | jq -r '.networkInterfaces[0].accessConfigs[0].natIP // "None"')
INTERNAL_IP=$(echo "$VM_INFO" | jq -r '.networkInterfaces[0].networkIP')

# Get disk information
DISKS=$(echo "$VM_INFO" | jq -r '.disks[] | "\(.deviceName): \(.diskSizeGb)GB (\(.type | split("/")[-1]))"')

echo "🖥️ VM Configuration:"
echo "   Status: $STATUS"
echo "   Machine Type: $MACHINE_TYPE"
echo "   Zone: $ZONE_FULL"
echo "   External IP: $EXTERNAL_IP"
echo "   Internal IP: $INTERNAL_IP"
echo ""

echo "💾 Attached Disks:"
echo "$DISKS" | sed 's/^/   /'
echo ""

# Estimate costs
echo "💰 Estimated Costs (per hour):"
case $MACHINE_TYPE in
    "e2-micro")
        echo "   ~$0.01/hour (Free tier eligible: 744 hours/month free)"
        echo "   ~$7.30/month (if exceeding free tier)"
        ;;
    "e2-small")
        echo "   ~$0.02/hour"
        echo "   ~$14.60/month"
        ;;
    "e2-medium")
        echo "   ~$0.03/hour"
        echo "   ~$21.90/month"
        ;;
    "e2-standard-2")
        echo "   ~$0.07/hour"
        echo "   ~$51.10/month"
        ;;
    "e2-standard-4")
        echo "   ~$0.13/hour"
        echo "   ~$94.90/month"
        ;;
    "c2-standard-4")
        echo "   ~$0.20/hour (High-performance)"
        echo "   ~$146.00/month"
        ;;
    "c2-standard-8")
        echo "   ~$0.40/hour (Ultra high-performance)"
        echo "   ~$292.00/month"
        ;;
    *)
        echo "   Cost information not available for $MACHINE_TYPE"
        ;;
esac

echo ""
echo "📈 Performance Level:"
case $MACHINE_TYPE in
    "e2-micro")
        echo "   🐌 Basic (1 vCPU) - Good for monitoring, light tasks"
        echo "   ⏱️ Backtesting: Very slow (12+ hours for comprehensive tests)"
        ;;
    "e2-small"|"e2-medium")
        echo "   🚶 Standard (2 vCPUs) - Good for regular operation"
        echo "   ⏱️ Backtesting: Slow (6-8 hours for comprehensive tests)"
        ;;
    "e2-standard-"*)
        echo "   🏃 Enhanced - Good for moderate workloads"
        echo "   ⏱️ Backtesting: Moderate (3-4 hours for comprehensive tests)"
        ;;
    "c2-standard-4")
        echo "   🚀 High-performance (4 high-perf vCPUs) - Excellent for backtesting"
        echo "   ⏱️ Backtesting: Fast (1-2 hours for comprehensive tests)"
        ;;
    "c2-standard-8")
        echo "   🏎️ Ultra high-performance (8 high-perf vCPUs) - Maximum speed"
        echo "   ⏱️ Backtesting: Very fast (30-60 minutes for comprehensive tests)"
        ;;
    *)
        echo "   Performance information not available for $MACHINE_TYPE"
        ;;
esac

echo ""
echo "🎯 Recommendations:"
if [[ "$MACHINE_TYPE" == "c2-standard-"* ]]; then
    echo "   ⚠️ You're using a high-performance (expensive) machine type"
    echo "   💡 Consider scaling down after backtesting: ./scripts/vm_scale_down.sh"
elif [[ "$MACHINE_TYPE" == "e2-micro" ]] || [[ "$MACHINE_TYPE" == "e2-small" ]]; then
    echo "   ✅ You're using a cost-effective machine type"
    echo "   🚀 For faster backtesting, scale up: ./scripts/vm_scale_up.sh"
else
    echo "   ⚖️ You're using a balanced machine type"
    echo "   🚀 For faster backtesting, scale up: ./scripts/vm_scale_up.sh"
    echo "   💰 For cost savings, scale down: ./scripts/vm_scale_down.sh"
fi

echo ""
echo "🔗 Connect to VM:"
if [ "$EXTERNAL_IP" != "None" ]; then
    echo "   ssh markus@$EXTERNAL_IP"
else
    echo "   No external IP assigned"
fi

echo ""
echo "📊 Available scaling commands:"
echo "   ./scripts/vm_scale_up.sh   - Scale up for heavy backtesting"
echo "   ./scripts/vm_scale_down.sh - Scale down to save costs"
echo "   ./scripts/vm_status.sh     - Show this status information"