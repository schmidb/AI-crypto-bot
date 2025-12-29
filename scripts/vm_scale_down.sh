#!/bin/bash
"""
Scale Down Google VM to Save Costs

This script scales your VM back down to a cost-effective machine type
after completing heavy backtesting work.

IMPORTANT: This preserves your attached disk and all data.
"""

set -e  # Exit on any error

# Configuration - UPDATE THESE VALUES
VM_NAME="${VM_NAME:-aicryptobot}"
ZONE="${ZONE:-us-central1-a}"
PROJECT="${PROJECT:-intense-base-456414-u5}"

# Cost-effective machine types
MICRO_MACHINE_TYPE="e2-micro"        # 1 vCPU, ~$0.01/hour (free tier eligible)
SMALL_MACHINE_TYPE="e2-small"       # 2 vCPUs, ~$0.02/hour
MEDIUM_MACHINE_TYPE="e2-medium"     # 2 vCPUs, more memory, ~$0.03/hour

echo "💰 VM Scale-Down Script for Cost Savings"
echo "========================================"
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

# Check if already cost-effective
if [[ "$CURRENT_MACHINE_TYPE" == "e2-micro" ]] || [[ "$CURRENT_MACHINE_TYPE" == "e2-small" ]]; then
    echo "✅ VM is already using cost-effective machine type: $CURRENT_MACHINE_TYPE"
    echo "No scaling needed."
    exit 0
fi

# Calculate potential savings
CURRENT_COST="Unknown"
if [[ "$CURRENT_MACHINE_TYPE" == "c2-standard-4" ]]; then
    CURRENT_COST="~$0.20/hour"
elif [[ "$CURRENT_MACHINE_TYPE" == "c2-standard-8" ]]; then
    CURRENT_COST="~$0.40/hour"
fi

echo ""
echo "💡 Current cost: $CURRENT_COST"
echo ""
echo "🎯 Choose cost-effective machine type:"
echo "1) e2-micro (1 vCPU, ~$0.01/hour) - Free tier eligible, good for light monitoring"
echo "2) e2-small (2 vCPUs, ~$0.02/hour) - Better performance, still very cheap"
echo "3) e2-medium (2 vCPUs + more memory, ~$0.03/hour) - Best balance for regular use"
echo "4) Cancel"
echo ""
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        TARGET_MACHINE_TYPE=$MICRO_MACHINE_TYPE
        NEW_COST="~$0.01/hour (Free tier eligible)"
        ;;
    2)
        TARGET_MACHINE_TYPE=$SMALL_MACHINE_TYPE
        NEW_COST="~$0.02/hour"
        ;;
    3)
        TARGET_MACHINE_TYPE=$MEDIUM_MACHINE_TYPE
        NEW_COST="~$0.03/hour"
        ;;
    4)
        echo "Cancelled."
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "🔧 Scaling VM down to: $TARGET_MACHINE_TYPE ($NEW_COST)"
echo ""

# Confirm the action
read -p "⚠️ This will restart your VM. Continue? (y/N): " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

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
echo "💰 VM Successfully Scaled Down!"
echo "==============================="
echo "VM Name: $VM_NAME"
echo "New Machine Type: $TARGET_MACHINE_TYPE"
echo "Status: RUNNING"
echo "External IP: $EXTERNAL_IP"
echo "New Cost: $NEW_COST"
echo ""
echo "🔗 Connect to your VM:"
echo "ssh markus@$EXTERNAL_IP"
echo ""
echo "✅ Cost savings achieved!"
if [[ "$TARGET_MACHINE_TYPE" == "e2-micro" ]]; then
    echo "💡 Your VM is now free tier eligible (if within limits)"
fi
echo ""
echo "📊 Your data and applications are preserved on the attached disk."
echo "🚀 When you need high performance again, run: ./scripts/vm_scale_up.sh"