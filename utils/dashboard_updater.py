    def _generate_charts(self, trading_data: Dict[str, Any], portfolio: Dict[str, Any]) -> None:
        """Generate charts for the dashboard"""
        try:
            # Create charts directory if it doesn't exist
            charts_dir = os.path.join(self.dashboard_dir, "images")
            os.makedirs(charts_dir, exist_ok=True)
            
            # Generate portfolio allocation chart
            self._generate_allocation_chart(portfolio, charts_dir)
            
            # Generate price charts for each trading pair
            for product_id in trading_data.get("prices", {}):
                self._generate_price_chart(product_id, trading_data["prices"][product_id], charts_dir)
                
        except Exception as e:
            logger.error(f"Error generating charts: {e}")
    
    def _generate_allocation_chart(self, portfolio: Dict[str, Any], charts_dir: str) -> None:
        """Generate portfolio allocation chart"""
        try:
            # Get target allocation from config
            from config import TARGET_ALLOCATION
            
            # Calculate current allocations
            current_allocations = {}
            total_value = portfolio.get("portfolio_value_usd", 0)
            
            if total_value > 0:
                for asset in ["BTC", "ETH", "USD"]:
                    if asset in portfolio:
                        asset_data = portfolio[asset]
                        amount = asset_data.get("amount", 0)
                        
                        # Calculate USD value
                        if asset == "USD":
                            value_usd = amount
                        else:
                            price = asset_data.get("last_price_usd", 0)
                            value_usd = amount * price
                        
                        # Calculate allocation percentage
                        current_allocations[asset] = round((value_usd / total_value) * 100, 2)
            
            # Create figure with two subplots
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
            
            # Current allocation pie chart
            labels = list(current_allocations.keys())
            sizes = list(current_allocations.values())
            ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            ax1.axis('equal')
            ax1.set_title('Current Allocation')
            
            # Target allocation pie chart
            target_labels = list(TARGET_ALLOCATION.keys())
            target_sizes = [TARGET_ALLOCATION[asset] for asset in target_labels]
            ax2.pie(target_sizes, labels=target_labels, autopct='%1.1f%%', startangle=90)
            ax2.axis('equal')
            ax2.set_title('Target Allocation')
            
            # Save chart
            plt.tight_layout()
            plt.savefig(os.path.join(charts_dir, "allocation_chart.png"))
            plt.close()
            
        except Exception as e:
            logger.error(f"Error generating allocation chart: {e}")
