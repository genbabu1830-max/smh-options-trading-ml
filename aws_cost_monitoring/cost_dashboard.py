#!/usr/bin/env python3
"""
AWS Cost Dashboard
Creates visual dashboard of costs over time
"""

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os


def create_dashboard():
    """Create visual cost dashboard"""
    
    csv_file = 'aws_cost_monitoring/data/daily_costs.csv'
    
    if not os.path.exists(csv_file):
        print("❌ No cost data found. Run check_daily_cost.py first.")
        return
    
    # Load data
    df = pd.read_csv(csv_file)
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('AWS Cost Dashboard - SMH Options Trading', fontsize=16, fontweight='bold')
    
    # 1. Daily Total Cost Trend
    total_df = df[df['Service'] == 'TOTAL'].copy()
    axes[0, 0].plot(total_df['Date'], total_df['Cost'], marker='o', linewidth=2)
    axes[0, 0].axhline(y=1.67, color='r', linestyle='--', label='Daily Target ($1.67)')
    axes[0, 0].set_title('Daily Total Cost')
    axes[0, 0].set_xlabel('Date')
    axes[0, 0].set_ylabel('Cost ($)')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. Cost by Service (Stacked Area)
    service_df = df[df['Service'] != 'TOTAL'].pivot(index='Date', columns='Service', values='Cost').fillna(0)
    service_df.plot(kind='area', stacked=True, ax=axes[0, 1], alpha=0.7)
    axes[0, 1].set_title('Cost by Service (Stacked)')
    axes[0, 1].set_xlabel('Date')
    axes[0, 1].set_ylabel('Cost ($)')
    axes[0, 1].legend(loc='upper left', fontsize=8)
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. Service Cost Distribution (Pie Chart)
    service_totals = df[df['Service'] != 'TOTAL'].groupby('Service')['Cost'].sum()
    axes[1, 0].pie(service_totals, labels=service_totals.index, autopct='%1.1f%%', startangle=90)
    axes[1, 0].set_title('Total Cost Distribution by Service')
    
    # 4. Monthly Projection
    last_7_days = total_df.tail(7)['Cost'].mean()
    monthly_projection = last_7_days * 30
    
    categories = ['Last 7 Days\nAverage', 'Monthly\nProjection', 'Budget\nTarget']
    values = [last_7_days, monthly_projection, 50.0]
    colors = ['green' if monthly_projection < 50 else 'orange', 
              'green' if monthly_projection < 50 else 'red', 
              'blue']
    
    bars = axes[1, 1].bar(categories, values, color=colors, alpha=0.7)
    axes[1, 1].set_title('Cost Projection vs Budget')
    axes[1, 1].set_ylabel('Cost ($)')
    axes[1, 1].axhline(y=50, color='r', linestyle='--', label='Budget Limit')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        axes[1, 1].text(bar.get_x() + bar.get_width()/2., height,
                       f'${height:.2f}',
                       ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    
    # Save dashboard
    output_dir = 'aws_cost_monitoring/reports'
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = f'{output_dir}/cost_dashboard_{datetime.now().strftime("%Y%m%d")}.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    
    print(f"📊 Dashboard saved to {output_file}")
    
    # Show dashboard
    plt.show()


if __name__ == '__main__':
    create_dashboard()
