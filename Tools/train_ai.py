#!/usr/bin/env python3
"""
AI Training Script for Camera Cursor System
Helps users train the intelligence engine with their preferences
"""

import pickle
import time
import os
from collections import defaultdict
import json

def load_existing_data():
    """Load existing learning data"""
    if os.path.exists('learning_data.pkl'):
        try:
            with open('learning_data.pkl', 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Error loading existing data: {e}")
    return []

def save_training_data(data):
    """Save training data"""
    try:
        with open('learning_data.pkl', 'wb') as f:
            pickle.dump(data, f)
        print("Training data saved successfully!")
    except Exception as e:
        print(f"Error saving training data: {e}")

def create_training_scenarios():
    """Create predefined training scenarios"""
    scenarios = [
        {
            'name': 'Web Browsing',
            'context': 'browsing',
            'mode': 'browsing',
            'description': 'Training for web browser usage',
            'samples': 20
        },
        {
            'name': 'Gaming',
            'context': 'gaming',
            'mode': 'gaming',
            'description': 'Training for gaming applications',
            'samples': 20
        },
        {
            'name': 'Coding/Text Editing',
            'context': 'typing',
            'mode': 'typing',
            'description': 'Training for coding and text editing',
            'samples': 20
        },
        {
            'name': 'Presentation',
            'context': 'presentation',
            'mode': 'presentation',
            'description': 'Training for presentation software',
            'samples': 15
        }
    ]
    return scenarios

def generate_training_data(scenario):
    """Generate synthetic training data for a scenario"""
    training_data = []

    print(f"\n🎯 Generating training data for: {scenario['name']}")
    print(f"📝 {scenario['description']}")

    # Simulate cursor positions for different regions
    regions = ['left', 'center', 'right', 'top', 'bottom']
    screen_width, screen_height = 1920, 1080  # Assume common resolution

    for i in range(scenario['samples']):
        # Generate cursor positions based on scenario
        if scenario['context'] == 'browsing':
            # Browsers often use left side for navigation
            x = int(screen_width * (0.1 + 0.3 * (i / scenario['samples'])))
            y = int(screen_height * (0.2 + 0.6 * (i / scenario['samples'])))
            region = 'left' if x < screen_width // 3 else 'center'
        elif scenario['context'] == 'gaming':
            # Gaming often uses center and right areas
            x = int(screen_width * (0.4 + 0.5 * (i / scenario['samples'])))
            y = int(screen_height * (0.3 + 0.5 * (i / scenario['samples'])))
            region = 'right' if x > 2 * screen_width // 3 else 'center'
        elif scenario['context'] == 'typing':
            # Text editing uses center-bottom areas
            x = int(screen_width * (0.3 + 0.4 * (i / scenario['samples'])))
            y = int(screen_height * (0.6 + 0.3 * (i / scenario['samples'])))
            region = 'bottom' if y > 2 * screen_height // 3 else 'center'
        elif scenario['context'] == 'presentation':
            # Presentations use center areas
            x = int(screen_width * (0.4 + 0.2 * (i / scenario['samples'])))
            y = int(screen_height * (0.3 + 0.4 * (i / scenario['samples'])))
            region = 'center'

        # Create training sample
        sample = {
            'cursor_pos': (x, y),
            'mode': scenario['mode'],
            'context': scenario['context'],
            'timestamp': time.time() - (scenario['samples'] - i) * 60,  # Spread over time
            'screen_region': region
        }

        training_data.append(sample)

        # Progress indicator
        if (i + 1) % 5 == 0:
            print(f"  Progress: {i + 1}/{scenario['samples']} samples generated")

    return training_data

def analyze_training_data(data):
    """Analyze the training data and provide insights"""
    if not data:
        print("No training data to analyze.")
        return

    print(f"\n📊 Training Data Analysis:")
    print(f"   Total samples: {len(data)}")

    # Analyze by context
    contexts = defaultdict(int)
    modes = defaultdict(int)
    regions = defaultdict(int)

    for sample in data:
        contexts[sample['context']] += 1
        modes[sample['mode']] += 1
        regions[sample['screen_region']] += 1

    print("   By Context:")
    for context, count in contexts.items():
        print(f"     {context}: {count} samples")

    print("   By Mode:")
    for mode, count in modes.items():
        print(f"     {mode}: {count} samples")

    print("   By Screen Region:")
    for region, count in regions.items():
        print(f"     {region}: {count} samples")

def main():
    print("🤖 Camera Cursor AI Training System")
    print("=" * 40)

    # Load existing data
    existing_data = load_existing_data()
    print(f"📂 Loaded {len(existing_data)} existing training samples")

    # Create scenarios
    scenarios = create_training_scenarios()

    print("
🎯 Available Training Scenarios:"    for i, scenario in enumerate(scenarios, 1):
        print(f"   {i}. {scenario['name']} - {scenario['description']}")

    print("
❓ What would you like to do?"    print("   1. Generate training data for all scenarios")
    print("   2. Generate training data for specific scenario")
    print("   3. Analyze current training data")
    print("   4. Clear all training data")
    print("   5. Exit")

    choice = input("\nEnter your choice (1-5): ").strip()

    if choice == '1':
        # Generate data for all scenarios
        all_training_data = existing_data.copy()

        for scenario in scenarios:
            new_data = generate_training_data(scenario)
            all_training_data.extend(new_data)

        save_training_data(all_training_data)
        analyze_training_data(all_training_data)

    elif choice == '2':
        # Generate data for specific scenario
        print("\nSelect a scenario:")
        for i, scenario in enumerate(scenarios, 1):
            print(f"   {i}. {scenario['name']}")

        try:
            scenario_choice = int(input("\nEnter scenario number: ")) - 1
            if 0 <= scenario_choice < len(scenarios):
                scenario = scenarios[scenario_choice]
                new_data = generate_training_data(scenario)

                all_training_data = existing_data + new_data
                save_training_data(all_training_data)
                analyze_training_data(all_training_data)
            else:
                print("Invalid scenario number.")
        except ValueError:
            print("Invalid input.")

    elif choice == '3':
        # Analyze data
        analyze_training_data(existing_data)

    elif choice == '4':
        # Clear data
        confirm = input("Are you sure you want to clear all training data? (yes/no): ").lower()
        if confirm == 'yes':
            save_training_data([])
            print("Training data cleared.")
        else:
            print("Operation cancelled.")

    elif choice == '5':
        print("Goodbye!")
        return

    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()
