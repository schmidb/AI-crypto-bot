#!/bin/bash
"""
Scale Up Google VM for Heavy Backtesting

This script scales up your VM to a high-performance machine type
for running comprehensive backtests, then provides commands to scale back down.

IMPORTANT: This preserves your attached disk and all data.
"""

set -e  # Exit on any error

# Configuration - UPDATE THESE VALUES
VM_NAME="${VM_NAME:-aicryptobot}"
ZONE="${ZONE:-us-central1-c}"
PROJECT="${PROJECT:-intense-base-456414-u5}"

# High-performance machine types
HIGH_PERF_MACHINE_TYPE="c2-standard-4"    # 4 high-performance vCPUs
ULTRA_PERF_MACHINE_TYPE="c2-standard-8"   # 8 high-performance vCPUs

echo "🚀 VM Scale-Up Script for Heavy Backtesting"
echo "============================================="
echo "VM Name: $VM_NAME"
echo "Zone: $ZONE"
echo "Project: $PROJECT"
echo ""

# Check if VM exists and get current status
echo "📋 Checking current VM status..."
CURRENT_STATUS=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --project=$PROJECT --format="value(status)" 2>/dev/null || echo "NOT_FOUND")

if [ "$CURRENT_STATUS" = "NOT_FOUND" ]; then
    echo "❌ VM '$VM_NAME' not found in zone '$ZONE'"
    echo "Please check your VM name and zone settings."
    exit 1
fi

# Get current machine type
CURRENT_MACHINE_TYPE=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --project=$PROJECT --format="value(machineType)" | sed 's|.*/||')
echo "Current machine type: $CURRENT_MACHINE_TYPE"
echo "Current status: $CURRENT_STATUS"

# Check if already high-performance
if [[ "$CURRENT_MACHINE_TYPE" == "c2-standard-"* ]]; then
    echo "✅ VM is already using high-performance machine type: $CURRENT_MACHINE_TYPE"
    echo "No scaling needed."
    exit 0
fi

# Offer machine type options
echo ""
echo "🎯 Choose scaling option:"
echo "1) c2-standard-4 (4 vCPUs, ~$0.20/hour) - Recommended for most backtests"
echo "2) c2-standard-8 (8 vCPUs, ~$0.40/hour) - For fastest processing"
echo "3) Cancel"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        TARGET_MACHINE_TYPE=$HIGH_PERF_MACHINE_TYPE
        COST_PER_HOUR="~$0.20"
        ;;
    2)
        TARGET_MACHINE_TYPE=$ULTRA_PERF_MACHINE_TYPE
        COST_PER_HOUR="~$0.40"
        ;;
    3)
        echo "Cancelled."
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "🔧 Scaling VM to: $TARGET_MACHINE_TYPE ($COST_PER_HOUR per hour)"
echo ""

# Stop VM if running
if [ "$CURRENT_STATUS" = "RUNNING" ]; then
    echo "⏹️ Stopping VM..."
    gcloud compute instances stop $VM_NAME --zone=$ZONE --project=$PROJECT --quiet
    
    echo "⏳ Waiting for VM to stop..."
    while true; do
        STATUS=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --project=$PROJECT --format="value(status)")
        if [ "$STATUS" = "TERMINATED" ]; then
            break
        fi
        echo "   Status: $STATUS (waiting...)"
        sleep 5
    done
    echo "✅ VM stopped successfully"
fi

# Change machine type
echo "🔄 Changing machine type to $TARGET_MACHINE_TYPE..."
gcloud compute instances set-machine-type $VM_NAME \
    --machine-type=$TARGET_MACHINE_TYPE \
    --zone=$ZONE \
    --project=$PROJECT

echo "✅ Machine type changed successfully"

# Start VM
echo "▶️ Starting VM with new machine type..."
gcloud compute instances start $VM_NAME --zone=$ZONE --project=$PROJECT --quiet

echo "⏳ Waiting for VM to start..."
while true; do
    STATUS=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --project=$PROJECT --format="value(status)")
    if [ "$STATUS" = "RUNNING" ]; then
        break
    fi
    echo "   Status: $STATUS (waiting...)"
    sleep 5
done

# Get external IP
EXTERNAL_IP=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --project=$PROJECT --format="value(networkInterfaces[0].accessConfigs[0].natIP)")

echo ""
echo "🎉 VM Successfully Scaled Up!"
echo "=============================="
echo "VM Name: $VM_NAME"
echo "New Machine Type: $TARGET_MACHINE_TYPE"
echo "Status: RUNNING"
echo "External IP: $EXTERNAL_IP"
echo "Estimated Cost: $COST_PER_HOUR per hour"
echo ""
echo "🔗 Connect to your VM:"
echo "ssh markus@$EXTERNAL_IP"
echo ""
echo "⚠️ IMPORTANT: Remember to scale down when done!"
echo "Run: ./scripts/vm_scale_down.sh"
echo ""
echo "💡 Recommended next steps:"
echo "1. SSH into your VM"
echo "2. cd ~/AI-crypto-bot"
echo "3. source venv/bin/activate"
echo "4. Run your backtests (they should be 4-8x faster now)"
echo "5. Scale down when complete to save costs"