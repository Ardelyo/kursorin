#!/usr/bin/env python3
"""
AI Insights Viewer for Camera Cursor System
View and analyze your AI learning data
"""

import pickle
import os
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import numpy as np

def load_learning_data():
    """Load learning data"""
    if os.path.exists('learning_data.pkl'):
        try:
            with open('learning_data.pkl', 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Error loading learning data: {e}")
    return []

def analyze_patterns(data):
    """Analyze learning patterns"""
    if not data:
        print("No learning data available.")
        return None

    # Basic statistics
    total_samples = len(data)

    # Context distribution
    contexts = Counter(sample['context'] for sample in data)
    modes = Counter(sample['mode'] for sample in data)
    regions = Counter(sample['screen_region'] for sample in data)

    # Time-based analysis
    timestamps = [sample['timestamp'] for sample in data]
    if timestamps:
        time_span = max(timestamps) - min(timestamps)
        hours_learned = time_span / 3600
    else:
        hours_learned = 0

    # Mode prediction accuracy (simulated)
    mode_predictions = {}
    for context in contexts.keys():
        context_modes = [s['mode'] for s in data if s['context'] == context]
        if context_modes:
            most_common = Counter(context_modes).most_common(1)[0]
            mode_predictions[context] = {
                'predicted_mode': most_common[0],
                'confidence': most_common[1] / len(context_modes),
                'total_samples': len(context_modes)
            }

    return {
        'total_samples': total_samples,
        'hours_learned': hours_learned,
        'contexts': dict(contexts),
        'modes': dict(modes),
        'regions': dict(regions),
        'predictions': mode_predictions
    }

def display_insights(insights):
    """Display insights in a readable format"""
    print("🧠 AI Learning Insights")
    print("=" * 50)

    print(f"📊 Total Learning Samples: {insights['total_samples']}")
    print(".1f"
    print(f"🎯 Context Distribution:")
    for context, count in insights['contexts'].items():
        percentage = (count / insights['total_samples']) * 100
        print(".1f"
    print(f"\n🎮 Mode Usage:")
    for mode, count in insights['modes'].items():
        percentage = (count / insights['total_samples']) * 100
        print(".1f"
    print(f"\n🖥️  Screen Region Usage:")
    for region, count in insights['regions'].items():
        percentage = (count / insights['total_samples']) * 100
        print(".1f"
    print(f"\n🔮 AI Predictions:")
    for context, pred in insights['predictions'].items():
        print(f"   {context} → {pred['predicted_mode']} "
              ".1f"              f"(from {pred['total_samples']} samples)")

def suggest_improvements(insights):
    """Suggest improvements based on insights"""
    print("
💡 AI Improvement Suggestions:"    suggestions = []

    # Check sample distribution
    min_samples = min(insights['contexts'].values()) if insights['contexts'] else 0
    max_samples = max(insights['contexts'].values()) if insights['contexts'] else 0

    if max_samples > min_samples * 2:
        suggestions.append("Consider training more in underrepresented contexts")

    # Check learning time
    if insights['hours_learned'] < 1:
        suggestions.append("AI needs more learning time (at least 1 hour recommended)")
    elif insights['hours_learned'] < 5:
        suggestions.append("Good learning progress! Continue using the system")

    # Check mode variety
    if len(insights['modes']) < 3:
        suggestions.append("Try using different modes to improve AI adaptability")

    if not suggestions:
        suggestions.append("AI learning looks good! Keep using the system naturally.")

    for suggestion in suggestions:
        print(f"   • {suggestion}")

def create_visualizations(insights):
    """Create visual charts of the learning data"""
    try:
        # Create subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))

        # Context distribution
        contexts = list(insights['contexts'].keys())
        context_counts = list(insights['contexts'].values())
        ax1.bar(contexts, context_counts, color='skyblue')
        ax1.set_title('Context Distribution')
        ax1.set_ylabel('Samples')
        ax1.tick_params(axis='x', rotation=45)

        # Mode distribution
        modes = list(insights['modes'].keys())
        mode_counts = list(insights['modes'].values())
        ax2.bar(modes, mode_counts, color='lightgreen')
        ax2.set_title('Mode Usage')
        ax2.set_ylabel('Samples')
        ax2.tick_params(axis='x', rotation=45)

        # Region distribution
        regions = list(insights['regions'].keys())
        region_counts = list(insights['regions'].values())
        ax3.bar(regions, region_counts, color='coral')
        ax3.set_title('Screen Region Usage')
        ax3.set_ylabel('Samples')
        ax3.tick_params(axis='x', rotation=45)

        # Prediction confidence
        pred_contexts = list(insights['predictions'].keys())
        confidences = [insights['predictions'][c]['confidence'] for c in pred_contexts]
        ax4.bar(pred_contexts, confidences, color='purple')
        ax4.set_title('Prediction Confidence')
        ax4.set_ylabel('Confidence')
        ax4.set_ylim(0, 1)
        ax4.tick_params(axis='x', rotation=45)

        plt.tight_layout()
        plt.savefig('ai_learning_insights.png', dpi=150, bbox_inches='tight')
        print("
📈 Visual insights saved as 'ai_learning_insights.png'"        plt.show()

    except Exception as e:
        print(f"Could not create visualizations: {e}")

def main():
    print("🔍 AI Insights Viewer")
    print("=" * 30)

    # Load data
    data = load_learning_data()

    if not data:
        print("❌ No learning data found. Use the system first to generate insights.")
        print("💡 Run 'python camera_cursor_v4.py' to start learning.")
        return

    # Analyze data
    insights = analyze_patterns(data)

    if insights:
        # Display insights
        display_insights(insights)

        # Show suggestions
        suggest_improvements(insights)

        # Ask about visualizations
        try:
            create_viz = input("\n📊 Create visual charts? (y/n): ").lower().strip()
            if create_viz == 'y':
                create_visualizations(insights)
        except:
            pass

    print("\n✅ Analysis complete!")

if __name__ == "__main__":
    main()
