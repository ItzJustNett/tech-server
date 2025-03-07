import requests
import json
import os
from getpass import getpass
from tabulate import tabulate
import time
import sys
import tempfile
import webbrowser

# Configuration
API_URL = "http://localhost:5000/api"
TOKEN_FILE = ".auth_token"
APP_NAME = "Learning Garden"

# Helper functions
def load_token():
    """Load authentication token from file"""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            return f.read().strip()
    return None

def save_token(token):
    """Save authentication token to file"""
    with open(TOKEN_FILE, 'w') as f:
        f.write(token)

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(subtitle=None):
    """Print the app header"""
    clear_screen()
    print("=" * 60)
    print(f"🌱 {APP_NAME} - Learn & Grow 🌱".center(60))
    if subtitle:
        print(subtitle.center(60))
    print("=" * 60)
    print()

def make_request(endpoint, method='GET', data=None, auth_required=True, files=None):
    """Make an API request"""
    url = f"{API_URL}/{endpoint}"
    headers = {}
    
    if auth_required:
        token = load_token()
        if token:
            headers['Authorization'] = f'Bearer {token}'
        else:
            print("Authentication required. Please log in first.")
            return None
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            if files:
                # For file uploads
                if data:
                    response = requests.post(url, headers=headers, data=data, files=files)
                else:
                    response = requests.post(url, headers=headers, files=files)
            else:
                # For JSON data
                headers['Content-Type'] = 'application/json'
                response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            # Check if response is a file
            if 'content-disposition' in response.headers:
                return response  # Return the response object for file downloads
            return response.json()
        elif response.status_code == 401:
            print("Authentication failed. Please log in again.")
            if os.path.exists(TOKEN_FILE):
                os.remove(TOKEN_FILE)
            input("Press Enter to continue...")
            return None
        else:
            print(f"Error: {response.status_code}")
            if response.headers.get('Content-Type') == 'application/json':
                error = response.json()
                print(f"Message: {error.get('error', 'Unknown error')}")
            input("Press Enter to continue...")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
        input("Press Enter to continue...")
        return None

def login():
    """Handle user login"""
    print_header("Login to your account")
    username = input("Username: ")
    password = getpass("Password: ")
    
    data = {
        'username': username,
        'password': password
    }
    
    response = make_request('login', method='POST', data=data, auth_required=False)
    
    if response and 'token' in response:
        save_token(response['token'])
        print("\n✅ Login successful!")
        time.sleep(1)
        return True
    else:
        print("\n❌ Login failed. Please try again.")
        input("Press Enter to continue...")
        return False

def register():
    """Handle user registration"""
    print_header("Create a new account")
    username = input("Username: ")
    email = input("Email: ")
    password = getpass("Password: ")
    confirm = getpass("Confirm password: ")
    
    if password != confirm:
        print("\n❌ Passwords do not match!")
        input("Press Enter to continue...")
        return False
    
    data = {
        'username': username,
        'email': email,
        'password': password
    }
    
    response = make_request('register', method='POST', data=data, auth_required=False)
    
    if response and 'token' in response:
        save_token(response['token'])
        print("\n✅ Registration successful! Welcome to Learning Garden!")
        print("🎁 You've received 3 sunflower seeds and 1 fertilizer to start your garden!")
        time.sleep(2)
        return True
    else:
        print("\n❌ Registration failed. Please try again.")
        input("Press Enter to continue...")
        return False

# Learning features
def view_subjects():
    """View all learning subjects"""
    print_header("Learning Subjects")
    
    response = make_request('subjects', auth_required=False)
    
    if response and 'subjects' in response:
        subjects = response['subjects']
        if not subjects:
            print("No subjects available.")
        else:
            table_data = []
            for subject in subjects:
                table_data.append([
                    subject['id'],
                    f"{subject.get('icon', '📚')} {subject['name']}",
                    subject.get('description', '')
                ])
            
            headers = ["ID", "Subject", "Description"]
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
            
            subject_id = input("\nEnter subject ID to view courses (or press Enter to return): ")
            if subject_id:
                view_subject_courses(subject_id)
                return
    else:
        print("Failed to load subjects.")
    
    input("Press Enter to continue...")

def view_subject_courses(subject_id):
    """View courses for a specific subject"""
    print_header("Courses")
    
    response = make_request(f'subjects/{subject_id}/courses', auth_required=False)
    
    if response and 'courses' in response:
        courses = response['courses']
        if not courses:
            print(f"No courses available for this subject.")
        else:
            # Get subject info
            subject_response = make_request(f'subjects/{subject_id}', auth_required=False)
            subject_name = subject_response.get('name', 'Subject') if subject_response else 'Subject'
            
            print(f"Courses in {subject_name}")
            print("-" * (len(f"Courses in {subject_name}")))
            
            table_data = []
            for course in courses:
                progress = course.get('progress', {})
                if progress:
                    completed = len(progress.get('completed_lessons', []))
                    level = progress.get('level', 1)
                    course_progress = f"{completed} lessons | Level {level}"
                else:
                    course_progress = "Not started"
                
                table_data.append([
                    course['id'],
                    course['title'],
                    course['difficulty'],
                    course_progress
                ])
            
            headers = ["ID", "Title", "Difficulty", "Progress"]
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
            
            course_id = input("\nEnter course ID to view details (or press Enter to return): ")
            if course_id:
                view_course(course_id)
                return
    else:
        print(f"Failed to load courses for subject {subject_id}.")
    
    input("Press Enter to continue...")

def view_courses():
    """View all available courses"""
    print_header("Available Courses")
    
    response = make_request('courses', auth_required=False)
    
    if response and 'courses' in response:
        courses = response['courses']
        if not courses:
            print("No courses available.")
        else:
            table_data = []
            for course in courses:
                progress = course.get('progress', {})
                if progress:
                    completed = len(progress.get('completed_lessons', []))
                    level = progress.get('level', 1)
                    course_progress = f"{completed} lessons | Level {level}"
                else:
                    course_progress = "Not started"
                
                table_data.append([
                    course['id'],
                    course['title'],
                    course['subject_name'],
                    course['difficulty'],
                    course_progress
                ])
            
            headers = ["ID", "Title", "Subject", "Difficulty", "Progress"]
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
            
            course_id = input("\nEnter course ID to view details (or press Enter to return): ")
            if course_id:
                view_course(course_id)
                return
    else:
        print("Failed to load courses.")
    
    input("Press Enter to continue...")

def view_course(course_id):
    """View course details"""
    print_header("Course Details")
    
    response = make_request(f'courses/{course_id}')
    
    if response and 'id' in response:
        course = response
        print(f"Course: {course['title']}")
        print(f"Subject: {course['subject_name']}")
        print(f"Difficulty: {course['difficulty']}")
        print(f"Description: {course.get('description', '')}")
        
        if course.get('progress'):
            progress = course['progress']
            completed = len(progress.get('completed_lessons', []))
            total = len(course.get('lessons', []))
            percent = (completed / total * 100) if total > 0 else 0
            print(f"\nYour Progress: {completed}/{total} lessons ({percent:.1f}%)")
            print(f"XP Earned: {progress.get('xp', 0)}")
            print(f"Level: {progress.get('level', 1)}")
        
        print("\nLessons:")
        
        if 'lessons' in course and course['lessons']:
            table_data = []
            for i, lesson in enumerate(course['lessons']):
                # Check if lesson is completed
                status = "🔒 Locked"
                if course.get('progress') and lesson['id'] in course['progress'].get('completed_lessons', []):
                    status = "✅ Completed"
                elif i == 0 or (course.get('progress') and course['lessons'][i-1]['id'] in course['progress'].get('completed_lessons', [])):
                    status = "🔓 Available"
                
                table_data.append([
                    i+1,  # Lesson number
                    lesson['id'],
                    lesson['title'],
                    lesson.get('description', ''),
                    f"{lesson.get('xp_reward', 10)} XP",
                    status
                ])
            
            headers = ["#", "ID", "Title", "Description", "Reward", "Status"]
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
            
            lesson_id = input("\nEnter lesson ID to start (or press Enter to return): ")
            if lesson_id:
                # Check if lesson is available
                for row in table_data:
                    if row[1] == lesson_id:
                        if row[5] == "🔓 Available" or row[5] == "✅ Completed":
                            start_lesson(lesson_id)
                        else:
                            print("\n❌ This lesson is locked. Complete previous lessons first.")
                            input("Press Enter to continue...")
                            view_course(course_id)
                        return
        else:
            print("No lessons available for this course.")
    else:
        print(f"Failed to load course {course_id}.")
    
    input("Press Enter to continue...")

def start_lesson(lesson_id):
    """Start a lesson"""
    print_header("Lesson")
    
    response = make_request(f'lessons/{lesson_id}')
    
    if response and 'id' in response:
        lesson = response
        print(f"Lesson: {lesson['title']}")
        print(f"Description: {lesson.get('description', '')}")
        print(f"XP Reward: {lesson.get('xp_reward', 10)}")
        
        if 'exercises' in lesson and lesson['exercises']:
            input("\nPress Enter to start the exercises...")
            
            correct_count = 0
            total_count = len(lesson['exercises'])
            
            for i, exercise in enumerate(lesson['exercises']):
                clear_screen()
                print(f"Exercise {i+1} of {total_count}")
                print("-" * 40)
                
                if exercise['type'] == 'multiple_choice':
                    print(exercise['question'])
                    print()
                    
                    for j, option in enumerate(exercise['options']):
                        print(f"{j+1}. {option}")
                    
                    print()
                    choice = input("Enter your answer (number): ")
                    
                    try:
                        choice_idx = int(choice) - 1
                        if 0 <= choice_idx < len(exercise['options']):
                            answer = exercise['options'][choice_idx]
                            
                            check_response = make_request(
                                f'exercises/{exercise["id"]}/check',
                                method='POST',
                                data={'answer': answer}
                            )
                            
                            if check_response and 'correct' in check_response:
                                if check_response['correct']:
                                    print("\n✅ Correct!")
                                    correct_count += 1
                                else:
                                    print("\n❌ Incorrect!")
                                    print(f"Correct answer: {check_response['correct_answer']}")
                                
                                if check_response.get('explanation'):
                                    print(f"\nExplanation: {check_response['explanation']}")
                            else:
                                print("\nFailed to check answer.")
                        else:
                            print("\nInvalid choice!")
                    except ValueError:
                        print("\nPlease enter a valid number!")
                
                elif exercise['type'] == 'text_input':
                    print(exercise['question'])
                    print()
                    
                    answer = input("Your answer: ")
                    
                    check_response = make_request(
                        f'exercises/{exercise["id"]}/check',
                        method='POST',
                        data={'answer': answer}
                    )
                    
                    if check_response and 'correct' in check_response:
                        if check_response['correct']:
                            print("\n✅ Correct!")
                            correct_count += 1
                        else:
                            print("\n❌ Incorrect!")
                            print(f"Correct answer: {check_response['correct_answer']}")
                        
                        if check_response.get('explanation'):
                            print(f"\nExplanation: {check_response['explanation']}")
                    else:
                        print("\nFailed to check answer.")
                
                elif exercise['type'] == 'true_false':
                    print(exercise['question'])
                    print()
                    print("1. True")
                    print("2. False")
                    print()
                    
                    choice = input("Enter your answer (1 for True, 2 for False): ")
                    
                    try:
                        answer = True if choice == '1' else False
                        
                        check_response = make_request(
                            f'exercises/{exercise["id"]}/check',
                            method='POST',
                            data={'answer': answer}
                        )
                        
                        if check_response and 'correct' in check_response:
                            if check_response['correct']:
                                print("\n✅ Correct!")
                                correct_count += 1
                            else:
                                print("\n❌ Incorrect!")
                                print(f"Correct answer: {'True' if check_response['correct_answer'] else 'False'}")
                            
                            if check_response.get('explanation'):
                                print(f"\nExplanation: {check_response['explanation']}")
                        else:
                            print("\nFailed to check answer.")
                    except:
                        print("\nInvalid choice!")
                
                elif exercise['type'] == 'fill_blanks':
                    print(exercise['question'])
                    print()
                    
                    answer = input("Your answer: ")
                    
                    check_response = make_request(
                        f'exercises/{exercise["id"]}/check',
                        method='POST',
                        data={'answer': [answer]}  # Sending as an array
                    )
                    
                    if check_response and 'correct' in check_response:
                        if check_response['correct']:
                            print("\n✅ Correct!")
                            correct_count += 1
                        else:
                            print("\n❌ Incorrect!")
                            if isinstance(check_response['correct_answer'], list):
                                print(f"Correct answer: {check_response['correct_answer'][0]}")
                            else:
                                print(f"Correct answer: {check_response['correct_answer']}")
                        
                        if check_response.get('explanation'):
                            print(f"\nExplanation: {check_response['explanation']}")
                    else:
                        print("\nFailed to check answer.")
                
                input("\nPress Enter to continue...")
            
            # Complete the lesson
            clear_screen()
            print(f"Lesson complete! Score: {correct_count}/{total_count}")
            
            if correct_count > 0:
                complete_response = make_request(f'lessons/{lesson_id}/complete', method='POST', data={})
                
                if complete_response and 'success' in complete_response:
                    print(f"\n✨ You earned {complete_response['xp_earned']} XP!")
                    
                    if complete_response.get('gem_reward'):
                        print(f"💎 You earned {complete_response['gem_reward']} gems!")
                    
                    if complete_response.get('level_up'):
                        print(f"🎉 You leveled up to level {complete_response['course_level']}!")
                    
                    if complete_response.get('plants_watered'):
                        print(f"🌱 Your plants have been watered!")
                    
                    # Display new achievements
                    if complete_response.get('new_achievements'):
                        print("\n🏆 New Achievements Unlocked! 🏆")
                        for achievement in complete_response['new_achievements']:
                            print(f"- {achievement['name']}: {achievement['description']} (+{achievement['xp_bonus']} XP)")
                else:
                    print("\nFailed to update progress.")
            
            input("\nPress Enter to return to the course view...")
            view_course(lesson['course_id'])
            return
        else:
            print("No exercises available for this lesson.")
    else:
        print(f"Failed to load lesson {lesson_id}.")
    
    input("Press Enter to continue...")

def view_leaderboard():
    """View leaderboard"""
    print_header("🏆 Leaderboard 🏆")
    
    response = make_request('leaderboard', auth_required=False)
    
    if response and 'leaderboard' in response:
        leaderboard = response['leaderboard']
        
        if leaderboard:
            table_data = []
            for i, entry in enumerate(leaderboard):
                table_data.append([
                    i + 1,
                    entry['username'],
                    entry['xp'],
                    entry.get('plants', 0),
                    f"{entry.get('gems', 0)} 💎"
                ])
            
            headers = ["Rank", "User", "XP", "Plants", "Gems"]
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
        else:
            print("Leaderboard is empty.")
    else:
        print("Failed to load leaderboard.")
    
    input("\nPress Enter to continue...")

# Garden features
def view_garden():
    """View user's garden"""
    print_header("🌱 Your Garden 🌱")
    
    response = make_request('garden')
    
    if response and 'plots' in response:
        garden = response
        
        print(f"Garden Level: {garden['garden_level']}")
        print(f"Last Watered: {garden['last_watered']}")
        
        if garden.get('active_helpers'):
            print("\n🤖 Active Helpers:")
            for helper in garden['active_helpers']:
                print(f"  {helper['icon']} {helper['name']} - {helper['days_remaining']} days remaining")
        
        print("\n🌱 Garden Plots:")
        
        table_data = []
        for plot in garden['plots']:
            if plot['empty']:
                table_data.append([
                    plot['id'][:8] + "...",
                    "Empty",
                    "",
                    "",
                    "",
                    "Plant a seed"
                ])
            else:
                # Format progress bar
                progress = plot['progress']
                progress_bar = "▓" * (progress // 10) + "░" * (10 - progress // 10)
                
                # Format health bar
                health_percent = plot['health'] / plot['max_health'] * 100
                health_bar = "♥" * (int(health_percent) // 20 + 1)
                
                status = "Ready to harvest! 🌟" if plot['harvestable'] else f"{progress}% grown"
                if not plot['watered']:
                    status += " (Needs water! 💧)"
                
                table_data.append([
                    plot['id'][:8] + "...",
                    f"{plot['icon']} {plot['plant_name']}",
                    f"{plot['level_name']}",
                    f"{progress_bar} {progress}%",
                    health_bar,
                    status
                ])
        
        headers = ["ID", "Plant", "Stage", "Growth", "Health", "Status"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        if garden.get('decorations'):
            print("\n🪴 Garden Decorations:")
            for decoration in garden['decorations']:
                print(f"  {decoration['icon']} {decoration['name']}")
        
        print("\nActions:")
        print("1. Water garden")
        print("2. Plant a seed")
        print("3. Harvest plants")
        print("4. Return to main menu")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == '1':
            water_garden()
        elif choice == '2':
            plant_seed()
        elif choice == '3':
            harvest_plants()
        
        return
    else:
        print("Failed to load garden.")
    
    input("Press Enter to continue...")

def water_garden():
    """Water all plants in the garden"""
    print_header("💧 Watering Garden 💧")
    
    response = make_request('garden/water', method='POST', data={})
    
    if response and 'success' in response:
        if response['success']:
            print(f"✅ {response['message']}")
            print(f"📊 Plants watered: {response['plants_watered']}")
            print(f"✨ XP earned: {response['xp_earned']}")
            
            if response.get('gem_reward'):
                print(f"💎 Gems found: {response['gem_reward']}")
        else:
            print(f"❌ {response['message']}")
    else:
        print("Failed to water garden.")
    
    input("Press Enter to return to garden...")
    view_garden()

def plant_seed():
    """Plant a seed in an empty plot"""
    print_header("🌱 Plant a Seed 🌱")
    
    # Get available seeds
    seeds_response = make_request('garden/seeds')
    
    if not seeds_response or 'seeds' not in seeds_response or not seeds_response['seeds']:
        print("❌ You don't have any seeds to plant.")
        input("Press Enter to return to garden...")
        view_garden()
        return
    
    # Get garden info
    garden_response = make_request('garden')
    
    if not garden_response or 'plots' not in garden_response:
        print("❌ Failed to load garden information.")
        input("Press Enter to return to garden...")
        view_garden()
        return
    
    # Find empty plots
    empty_plots = [plot for plot in garden_response['plots'] if plot['empty']]
    
    if not empty_plots:
        print("❌ You don't have any empty plots available.")
        input("Press Enter to return to garden...")
        view_garden()
        return
    
    # Display available seeds
    print("Available Seeds:")
    table_data = []
    for i, seed in enumerate(seeds_response['seeds']):
        table_data.append([
            i + 1,
            seed['id'],
            f"{seed['icon']} {seed['name']}",
            seed['description'],
            seed['quantity']
        ])
    
    headers = ["#", "ID", "Seed", "Description", "Quantity"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Display empty plots
    print("\nEmpty Plots:")
    plot_table = []
    for i, plot in enumerate(empty_plots):
        plot_table.append([
            i + 1,
            plot['id']
        ])
    
    plot_headers = ["#", "Plot ID"]
    print(tabulate(plot_table, headers=plot_headers, tablefmt="grid"))
    
    # Get user selection
    seed_choice = input("\nEnter seed number to plant (or 0 to cancel): ")
    
    if seed_choice == '0':
        view_garden()
        return
    
    try:
        seed_idx = int(seed_choice) - 1
        if seed_idx < 0 or seed_idx >= len(seeds_response['seeds']):
            print("❌ Invalid seed selection.")
            input("Press Enter to return to garden...")
            view_garden()
            return
        
        seed = seeds_response['seeds'][seed_idx]
        
        plot_choice = input(f"Enter plot number to plant {seed['name']} (or 0 to cancel): ")
        
        if plot_choice == '0':
            view_garden()
            return
        
        plot_idx = int(plot_choice) - 1
        if plot_idx < 0 or plot_idx >= len(empty_plots):
            print("❌ Invalid plot selection.")
            input("Press Enter to return to garden...")
            view_garden()
            return
        
        plot = empty_plots[plot_idx]
        
        # Plant the seed
        plant_response = make_request('garden/plant', method='POST', data={
            'plot_id': plot['id'],
            'seed_id': seed['id']
        })
        
        if plant_response and 'success' in plant_response:
            print(f"✅ {plant_response['message']}")
            if plant_response.get('xp_earned'):
                print(f"✨ XP earned: {plant_response['xp_earned']}")
        else:
            print("❌ Failed to plant seed.")
        
    except ValueError:
        print("❌ Please enter a valid number.")
    
    input("Press Enter to return to garden...")
    view_garden()

def harvest_plants():
    """Harvest mature plants"""
    print_header("🌾 Harvest Plants 🌾")
    
    # Get garden info
    garden_response = make_request('garden')
    
    if not garden_response or 'plots' not in garden_response:
        print("❌ Failed to load garden information.")
        input("Press Enter to return to garden...")
        view_garden()
        return
    
    # Find harvestable plots
    harvestable_plots = [plot for plot in garden_response['plots'] if not plot['empty'] and plot['harvestable']]
    
    if not harvestable_plots:
        print("❌ You don't have any plants ready to harvest.")
        input("Press Enter to return to garden...")
        view_garden()
        return
    
    # Display harvestable plants
    print("Ready to Harvest:")
    table_data = []
    for i, plot in enumerate(harvestable_plots):
        table_data.append([
            i + 1,
            plot['id'][:8] + "...",
            f"{plot['icon']} {plot['plant_name']}",
            plot['level_name']
        ])
    
    headers = ["#", "Plot ID", "Plant", "Stage"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Get user selection
    plot_choice = input("\nEnter plant number to harvest (or 0 to cancel): ")
    
    if plot_choice == '0':
        view_garden()
        return
    
    try:
        plot_idx = int(plot_choice) - 1
        if plot_idx < 0 or plot_idx >= len(harvestable_plots):
            print("❌ Invalid selection.")
            input("Press Enter to return to garden...")
            view_garden()
            return
        
        plot = harvestable_plots[plot_idx]
        
        # Harvest the plant
        harvest_response = make_request('garden/harvest', method='POST', data={
            'plot_id': plot['id']
        })
        
        if harvest_response and 'success' in harvest_response:
            print(f"✅ {harvest_response['message']}")
            
            if harvest_response.get('seed_returned'):
                print("🌱 You also received a seed!")
        else:
            print("❌ Failed to harvest plant.")
        
    except ValueError:
        print("❌ Please enter a valid number.")
    
    input("Press Enter to return to garden...")
    view_garden()

# Shop and economy features
def view_shop():
    """View shop items"""
    print_header("🛒 Shop 🛒")
    
    # Get shop items
    response = make_request('shop', auth_required=False)
    
    if response and 'shop_items' in response:
        shop_items = response['shop_items']
        user_gems = response.get('user_gems', 0)
        
        print(f"Your Balance: 💎 {user_gems} gems\n")
        
        # Group items by category
        categories = {}
        for item in shop_items:
            category = item['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(item)
        
        for category, items in categories.items():
            print(f"\n📦 {category.upper()}")
            table_data = []
            for i, item in enumerate(items):
                can_afford = user_gems >= item['price']
                price_display = f"💎 {item['price']}" if can_afford else f"💎 {item['price']} ❌"
                
                table_data.append([
                    len(table_data) + 1,
                    item['id'],
                    f"{item['icon']} {item['name']}",
                    item['description'],
                    price_display
                ])
            
            headers = ["#", "ID", "Item", "Description", "Price"]
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        item_number = input("\nEnter item number to purchase (or 0 to return): ")
        
        if item_number == '0':
            return
        
        try:
            item_idx = int(item_number) - 1
            if item_idx < 0 or item_idx >= len(shop_items):
                print("❌ Invalid item selection.")
                input("Press Enter to continue...")
                view_shop()
                return
            
            item = shop_items[item_idx]
            
            if user_gems < item['price']:
                print(f"❌ Not enough gems. You need {item['price']} gems but only have {user_gems}.")
                input("Press Enter to continue...")
                view_shop()
                return
            
            quantity = 1
            if item['category'] == 'seeds':
                try:
                    qty_input = input(f"How many {item['name']} do you want to buy? (default: 1): ")
                    if qty_input.strip():
                        quantity = int(qty_input)
                        if quantity <= 0:
                            print("❌ Quantity must be positive.")
                            input("Press Enter to continue...")
                            view_shop()
                            return
                except ValueError:
                    print("❌ Please enter a valid number.")
                    input("Press Enter to continue...")
                    view_shop()
                    return
            
            # Confirm purchase
            total_price = item['price'] * quantity
            confirm = input(f"Confirm purchase of {quantity}x {item['name']} for 💎 {total_price} gems? (y/n): ")
            
            if confirm.lower() == 'y':
                purchase_response = make_request('shop/purchase', method='POST', data={
                    'item_id': item['id'],
                    'quantity': quantity
                })
                
                if purchase_response and 'success' in purchase_response:
                    print(f"✅ {purchase_response['message']}")
                    print(f"💎 Gems remaining: {purchase_response['gems_remaining']}")
                else:
                    print("❌ Failed to complete purchase.")
            else:
                print("Purchase cancelled.")
            
            input("Press Enter to continue...")
            view_shop()
            return
            
        except ValueError:
            print("❌ Please enter a valid number.")
            input("Press Enter to continue...")
            view_shop()
            return
    else:
        print("Failed to load shop items.")
    
    input("Press Enter to continue...")

def view_inventory():
    """View user's inventory"""
    print_header("🎒 Inventory 🎒")
    
    response = make_request('inventory')
    
    if response and 'inventory' in response:
        inventory = response['inventory']
        
        for category, items in inventory.items():
            if not items:
                continue
                
            print(f"\n📦 {category.upper()}")
            table_data = []
            for i, item in enumerate(items):
                table_data.append([
                    i + 1,
                    item['id'],
                    f"{item['icon']} {item['name']}",
                    item['description'],
                    item['quantity'],
                    item['type']
                ])
            
            headers = ["#", "ID", "Item", "Description", "Quantity", "Type"]
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        if sum(len(items) for items in inventory.values()) == 0:
            print("Your inventory is empty.")
        else:
            item_number = input("\nEnter item number to use (or 0 to return): ")
            
            if item_number == '0':
                return
            
            try:
                # Find the item across all categories
                selected_item = None
                selected_category = None
                
                current_idx = 0
                for category, items in inventory.items():
                    for item in items:
                        current_idx += 1
                        if current_idx == int(item_number):
                            selected_item = item
                            selected_category = category
                            break
                    
                    if selected_item:
                        break
                
                if not selected_item:
                    print("❌ Invalid item selection.")
                    input("Press Enter to continue...")
                    view_inventory()
                    return
                
                # Confirm use
                confirm = input(f"Use {selected_item['name']}? (y/n): ")
                
                if confirm.lower() == 'y':
                    use_response = make_request('inventory/use', method='POST', data={
                        'item_id': selected_item['id']
                    })
                    
                    if use_response and 'success' in use_response:
                        print(f"✅ {use_response['message']}")
                    else:
                        print("❌ Failed to use item.")
                else:
                    print("Action cancelled.")
                
                input("Press Enter to continue...")
                view_inventory()
                return
                
            except ValueError:
                print("❌ Please enter a valid number.")
                input("Press Enter to continue...")
                view_inventory()
                return
    else:
        print("Failed to load inventory.")
    
    input("Press Enter to continue...")

def view_helpers():
    """View and manage helpers"""
    print_header("🤖 Helpers & Robots 🤖")
    
    response = make_request('helpers')
    
    if response:
        active_helpers = response.get('active_helpers', [])
        available_helpers = response.get('available_helpers', [])
        
        if active_helpers:
            print("🚀 Active Helpers")
            table_data = []
            for i, helper in enumerate(active_helpers):
                table_data.append([
                    i + 1,
                    helper['id'][:8] + "...",
                    f"{helper['icon']} {helper['name']}",
                    helper['effect_type'],
                    f"{helper['days_remaining']} days"
                ])
            
            headers = ["#", "ID", "Helper", "Effect", "Remaining"]
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
            
            print("\n1. Deactivate a helper")
        else:
            print("You don't have any active helpers.")
        
        if available_helpers:
            print("\n🔋 Available Helpers")
            avail_table = []
            for i, helper in enumerate(available_helpers):
                avail_table.append([
                    i + 1,
                    helper['id'],
                    f"{helper['icon']} {helper['name']}",
                    helper['description'],
                    helper['effect_type'],
                    f"{helper['duration']} days",
                    helper['quantity']
                ])
            
            avail_headers = ["#", "ID", "Helper", "Description", "Effect", "Duration", "Qty"]
            print(tabulate(avail_table, headers=avail_headers, tablefmt="grid"))
            
            print("\n2. Activate a helper")
        else:
            print("\nYou don't have any available helpers.")
        
        print("\n0. Return to main menu")
        
        choice = input("\nEnter your choice: ")
        
        if choice == '1' and active_helpers:
            helper_num = input("Enter helper number to deactivate: ")
            
            try:
                helper_idx = int(helper_num) - 1
                if helper_idx < 0 or helper_idx >= len(active_helpers):
                    print("❌ Invalid helper selection.")
                else:
                    helper = active_helpers[helper_idx]
                    
                    # Confirm deactivation
                    confirm = input(f"Deactivate {helper['name']}? This action cannot be undone. (y/n): ")
                    
                    if confirm.lower() == 'y':
                        deactivate_response = make_request('helpers/deactivate', method='POST', data={
                            'helper_id': helper['id']
                        })
                        
                        if deactivate_response and 'success' in deactivate_response:
                            print(f"✅ {deactivate_response['message']}")
                        else:
                            print("❌ Failed to deactivate helper.")
                    else:
                        print("Action cancelled.")
            except ValueError:
                print("❌ Please enter a valid number.")
            
            input("Press Enter to continue...")
            view_helpers()
            return
            
        elif choice == '2' and available_helpers:
            helper_num = input("Enter helper number to activate: ")
            
            try:
                helper_idx = int(helper_num) - 1
                if helper_idx < 0 or helper_idx >= len(available_helpers):
                    print("❌ Invalid helper selection.")
                else:
                    helper = available_helpers[helper_idx]
                    
                    # Use the inventory endpoint to activate the helper
                    use_response = make_request('inventory/use', method='POST', data={
                        'item_id': helper['id']
                    })
                    
                    if use_response and 'success' in use_response:
                        print(f"✅ {use_response['message']}")
                    else:
                        print("❌ Failed to activate helper.")
            except ValueError:
                print("❌ Please enter a valid number.")
            
            input("Press Enter to continue...")
            view_helpers()
            return
    else:
        print("Failed to load helpers.")
    
    input("Press Enter to continue...")

def view_economy():
    """View user's economic data"""
    print_header("💎 Economy 💎")
    
    # Get balance
    balance_response = make_request('economy/balance')
    
    if balance_response:
        print(f"💎 Gem Balance: {balance_response['gems']}")
        
        # Check for daily bonus
        last_daily = balance_response.get('last_daily_bonus')
        today = time.strftime('%Y-%m-%d')
        
        if last_daily != today:
            print("\n🎁 Daily bonus available!")
            claim = input("Claim daily bonus? (y/n): ")
            
            if claim.lower() == 'y':
                bonus_response = make_request('economy/daily-bonus', method='POST', data={})
                
                if bonus_response and 'success' in bonus_response:
                    print(f"✅ {bonus_response['message']}")
                    print(f"💎 Current balance: {bonus_response['current_balance']}")
                else:
                    print("❌ Failed to claim daily bonus.")
        else:
            print("\n✓ Daily bonus already claimed today.")
        
        # Get transaction history
        print("\nTransaction History:")
        transactions_response = make_request('economy/transactions')
        
        if transactions_response and 'transactions' in transactions_response:
            transactions = transactions_response['transactions']
            
            if transactions:
                table_data = []
                for i, tx in enumerate(transactions[:10]):  # Show only last 10
                    date = tx['date'].split('T')[0]
                    time_str = tx['date'].split('T')[1].split('.')[0]
                    
                    amount_str = f"+{tx['amount']}" if tx['type'] == 'credit' else f"-{tx['amount']}"
                    
                    table_data.append([
                        i + 1,
                        f"{date} {time_str}",
                        amount_str,
                        tx['reason'],
                        tx['balance']
                    ])
                
                headers = ["#", "Date/Time", "Amount", "Description", "Balance"]
                print(tabulate(table_data, headers=headers, tablefmt="grid"))
                
                if len(transactions) > 10:
                    print(f"Showing 10 of {len(transactions)} transactions.")
            else:
                print("No transactions yet.")
        else:
            print("Failed to load transaction history.")
    else:
        print("Failed to load economic data.")
    
    input("\nPress Enter to continue...")

def view_profile():
    """View user profile with combined stats"""
    print_header("👤 User Profile 👤")
    
    response = make_request('user/profile')
    
    if response and 'user' in response:
        user = response['user']
        learning = response['learning']
        garden = response['garden']
        economy = response['economy']
        inventory = response['inventory']
        
        print(f"Username: {user['username']}")
        print(f"Email: {user['email']}")
        print(f"Member since: {user['created_at'][:10]}")
        print()
        
        print("📊 STATS")
        print(f"🔢 Total XP: {learning['xp']}")
        print(f"🌱 Garden Level: {garden['level']}")
        print(f"🪴 Plants: {garden['plots_used']}/{garden['plots_total']} plots used")
        print(f"🌟 Mature plants: {garden['plants_mature']}")
        print(f"💧 Last watered: {garden['last_watered']}")
        print(f"💎 Gems: {economy['gems']}")
        print(f"🎒 Inventory items: {inventory['items_count']}")
        print()
        
        if learning.get('achievements'):
            print("🏆 ACHIEVEMENTS")
            for achievement in learning['achievements']:
                print(f"  {achievement['icon']} {achievement['name']}: {achievement['description']}")
            print()
        
        if learning.get('courses'):
            print("📚 COURSES PROGRESS")
            table_data = []
            for course in learning['courses']:
                progress_bar = "▓" * (course['percentage'] // 10) + "░" * (10 - course['percentage'] // 10)
                
                table_data.append([
                    course['course'],
                    course['subject'],
                    f"{course['completed_lessons']}/{course['total_lessons']}",
                    f"{progress_bar} {course['percentage']}%",
                    f"Level {course['level']} ({course['xp']} XP)"
                ])
            
            headers = ["Course", "Subject", "Completed", "Progress", "Level"]
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
    else:
        print("Failed to load profile.")
    
    input("\nPress Enter to continue...")

# Bot features
def generate_ai_response():
    """Generate AI response"""
    print_header("🤖 AI Generation 🤖")
    
    # Get AI models
    models_response = make_request('ai/models')
    
    if models_response and 'current_model' in models_response:
        current_model = models_response['current_model']
        current_model_name = current_model.split('/')[-1].split(':')[0]
        
        print(f"Current AI Model: {current_model_name}")
        print("\nOptions:")
        print("1. Generate response")
        print("2. Change AI model")
        print("0. Return to main menu")
        
        choice = input("\nEnter your choice: ")
        
        if choice == '1':
            print("\nEnter your prompt (type 'EXIT' on a new line to finish):")
            prompt_lines = []
            
            while True:
                line = input()
                if line == 'EXIT':
                    break
                prompt_lines.append(line)
            
            prompt = '\n'.join(prompt_lines)
            
            if not prompt.strip():
                print("❌ Prompt cannot be empty.")
                input("Press Enter to continue...")
                generate_ai_response()
                return
            
            print("\n🤖 Generating response...")
            
            response = make_request('generate', method='POST', data={
                'prompt': prompt
            })
            
            if response and 'response' in response:
                print("\n----- AI RESPONSE -----")
                print(response['response'])
                print("-----------------------")
            else:
                print("❌ Failed to generate response.")
            
            input("\nPress Enter to continue...")
            generate_ai_response()
            return
            
        elif choice == '2':
            if 'models' in models_response:
                models = models_response['models']
                
                print("\nAvailable AI Models:")
                table_data = []
                for i, model in enumerate(models):
                    current = "✓" if model['is_current'] else ""
                    
                    table_data.append([
                        i + 1,
                        model['name'],
                        model['description'],
                        current
                    ])
                
                headers = ["#", "Model", "Description", "Current"]
                print(tabulate(table_data, headers=headers, tablefmt="grid"))
                
                model_choice = input("\nEnter model number to select (or 0 to cancel): ")
                
                if model_choice == '0':
                    generate_ai_response()
                    return
                
                try:
                    model_idx = int(model_choice) - 1
                    if model_idx < 0 or model_idx >= len(models):
                        print("❌ Invalid model selection.")
                    else:
                        model = models[model_idx]
                        
                        # Set the model
                        set_response = make_request('ai/models', method='POST', data={
                            'model_id': model['id']
                        })
                        
                        if set_response and 'success' in set_response:
                            print(f"✅ {set_response['message']}")
                        else:
                            print("❌ Failed to change AI model.")
                except ValueError:
                    print("❌ Please enter a valid number.")
                
                input("Press Enter to continue...")
                generate_ai_response()
                return
    else:
        print("Failed to load AI models.")
    
    input("Press Enter to continue...")

def transcribe_url():
    """Transcribe audio/video from URL"""
    print_header("🎵 Transcribe Media 🎵")
    
    url = input("Enter URL to transcribe (YouTube, SoundCloud, etc.): ")
    
    if not url:
        print("❌ URL cannot be empty.")
        input("Press Enter to continue...")
        return
    
    language = input("Preferred language (en for English, uk for Ukrainian, or leave empty): ")
    
    print("\n🔄 Processing URL... This may take a few minutes depending on the media length.")
    
    data = {
        'url': url
    }
    
    if language:
        data['language'] = language
    
    response = make_request('transcribe/url', method='POST', data=data)
    
    if response and 'success' in response and response['success']:
        print(f"\n✅ Transcription successful!")
        print(f"Source: {response.get('source', 'unknown')}")
        
        if response.get('language'):
            print(f"Language: {response['language']}")
        
        if response.get('title'):
            print(f"Title: {response['title']}")
        
        if response.get('subtitle_type'):
            print(f"Subtitle type: {response['subtitle_type']}")
        
        print("\n----- TRANSCRIPT -----")
        transcript = response['transcript']
        
        # If transcript is very long, save to file
        if len(transcript) > 2000:
            filename = f"transcript_{int(time.time())}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(transcript)
            
            print(f"Transcript saved to file: {filename}")
            print(transcript[:2000] + "...\n[Content truncated, see file for complete transcript]")
        else:
            print(transcript)
        
        print("----------------------")
        
        # Ask if user wants to generate AI response
        ai_response = input("\nGenerate AI response based on transcript? (y/n): ")
        
        if ai_response.lower() == 'y':
            print("\n🤖 Generating AI response...")
            
            ai_data = {
                'prompt': f"Please summarize and analyze the following transcript:\n\n{transcript[:4000]}",
            }
            
            ai_response = make_request('generate', method='POST', data=ai_data)
            
            if ai_response and 'response' in ai_response:
                print("\n----- AI RESPONSE -----")
                print(ai_response['response'])
                print("-----------------------")
            else:
                print("❌ Failed to generate AI response.")
    else:
        print("❌ Failed to transcribe URL.")
    
    input("\nPress Enter to continue...")

def web_search():
    """Search the web"""
    print_header("🔍 Web Search 🔍")
    
    query = input("Enter search query: ")
    
    if not query:
        print("❌ Query cannot be empty.")
        input("Press Enter to continue...")
        return
    
    print("\n🔍 Searching the web... This may take a moment.")
    
    response = make_request('web/search', method='POST', data={
        'query': query
    })
    
    if response and 'success' in response and response['success']:
        print("\n✅ Search completed!")
        
        print("\n----- SEARCH RESULTS -----")
        result = response['result']
        
        # If result is very long, save to file
        if len(result) > 3000:
            filename = f"search_{int(time.time())}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(result)
            
            print(f"Search results saved to file: {filename}")
            print(result[:3000] + "...\n[Content truncated, see file for complete results]")
        else:
            print(result)
        
        print("--------------------------")
    else:
        print("❌ Failed to search the web.")
    
    input("\nPress Enter to continue...")

def text_to_speech():
    """Convert text to speech"""
    print_header("🔊 Text to Speech 🔊")
    
    print("Enter text to convert to speech (type 'EXIT' on a new line to finish):")
    text_lines = []
    
    while True:
        line = input()
        if line == 'EXIT':
            break
        text_lines.append(line)
    
    text = '\n'.join(text_lines)
    
    if not text.strip():
        print("❌ Text cannot be empty.")
        input("Press Enter to continue...")
        return
    
    print("\n🔄 Converting text to speech...")
    
    response = make_request('tts', method='POST', data={
        'text': text
    })
    
    if response:  # Response is a file
        # Save audio to a temporary file
        filename = f"speech_{int(time.time())}.mp3"
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Speech saved to file: {filename}")
        
        # Try to play the audio
        try:
            # Try to open the file with default audio player
            if sys.platform == 'win32':
                os.startfile(filename)
            elif sys.platform == 'darwin':
                os.system(f"open {filename}")
            else:
                os.system(f"xdg-open {filename}")
        except:
            print("Note: Could not automatically play the audio file.")
    else:
        print("❌ Failed to convert text to speech.")
    
    input("\nPress Enter to continue...")

def generate_pdf():
    """Generate PDF from text"""
    print_header("📄 Generate PDF 📄")
    
    title = input("Enter PDF title (optional): ")
    
    print("\nEnter text content (type 'EXIT' on a new line to finish):")
    content_lines = []
    
    while True:
        line = input()
        if line == 'EXIT':
            break
        content_lines.append(line)
    
    content = '\n'.join(content_lines)
    
    if not content.strip():
        print("❌ Content cannot be empty.")
        input("Press Enter to continue...")
        return
    
    print("\n🔄 Generating PDF...")
    
    data = {
        'text': content
    }
    
    if title:
        data['title'] = title
    
    response = make_request('pdf', method='POST', data=data)
    
    if response:  # Response is a file
        # Save PDF to a file
        filename = f"{title.replace(' ', '_')}_{int(time.time())}.pdf" if title else f"document_{int(time.time())}.pdf"
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ PDF saved to file: {filename}")
        
        # Try to open the PDF
        try:
            # Try to open the file with default PDF viewer
            if sys.platform == 'win32':
                os.startfile(filename)
            elif sys.platform == 'darwin':
                os.system(f"open {filename}")
            else:
                os.system(f"xdg-open {filename}")
        except:
            print("Note: Could not automatically open the PDF file.")
    else:
        print("❌ Failed to generate PDF.")
    
    input("\nPress Enter to continue...")

def transcribe_voice():
    """Transcribe a voice recording"""
    print_header("🎤 Transcribe Voice 🎤")
    
    print("Select a voice file from your computer.")
    filename = input("Enter path to voice file (must be .mp3, .wav, .ogg, etc.): ")
    
    if not filename or not os.path.exists(filename):
        print("❌ File not found.")
        input("Press Enter to continue...")
        return
    
    print("\n🔄 Transcribing voice... This may take a moment.")
    
    with open(filename, 'rb') as f:
        files = {'voice': (os.path.basename(filename), f)}
        response = make_request('transcribe/voice', method='POST', files=files, data={'generate_response': 'false'})
    
    if response and 'success' in response and response['success']:
        print("\n✅ Transcription successful!")
        
        print("\n----- TRANSCRIPTION -----")
        print(response['transcription'])
        print("--------------------------")
        
        # Ask if user wants to generate AI response
        ai_response = input("\nGenerate AI response based on transcription? (y/n): ")
        
        if ai_response.lower() == 'y':
            print("\n🤖 Generating AI response...")
            
            ai_data = {
                'prompt': response['transcription']
            }
            
            ai_response = make_request('generate', method='POST', data=ai_data)
            
            if ai_response and 'response' in ai_response:
                print("\n----- AI RESPONSE -----")
                print(ai_response['response'])
                print("-----------------------")
            else:
                print("❌ Failed to generate AI response.")
        
        if response.get('gem_reward'):
            print(f"\n💎 You found {response['gem_reward']} gems during transcription!")
    else:
        print("❌ Failed to transcribe voice.")
    
    input("\nPress Enter to continue...")

def main_menu():
    """Show main menu"""
    while True:
        print_header("Main Menu")
        print("🌱 Garden")
        print("1. View my garden")
        print("2. View inventory")
        print("3. Shop")
        print("4. Helpers & robots")
        print("5. View economy")
        print()
        print("📚 Learning")
        print("6. View subjects")
        print("7. View all courses")
        print("8. View leaderboard")
        print()
        print("🤖 AI & Tools")
        print("9. Generate AI response")
        print("10. Transcribe URL")
        print("11. Transcribe voice")
        print("12. Web search")
        print("13. Text to speech")
        print("14. Generate PDF")
        print()
        print("👤 User")
        print("15. View profile")
        print("16. Logout")
        print("17. Exit")
        print()
        
        choice = input("Enter your choice (1-17): ")
        
        if choice == '1':
            view_garden()
        elif choice == '2':
            view_inventory()
        elif choice == '3':
            view_shop()
        elif choice == '4':
            view_helpers()
        elif choice == '5':
            view_economy()
        elif choice == '6':
            view_subjects()
        elif choice == '7':
            view_courses()
        elif choice == '8':
            view_leaderboard()
        elif choice == '9':
            generate_ai_response()
        elif choice == '10':
            transcribe_url()
        elif choice == '11':
            transcribe_voice()
        elif choice == '12':
            web_search()
        elif choice == '13':
            text_to_speech()
        elif choice == '14':
            generate_pdf()
        elif choice == '15':
            view_profile()
        elif choice == '16':
            if os.path.exists(TOKEN_FILE):
                os.remove(TOKEN_FILE)
            print("\nYou have been logged out.")
            time.sleep(1)
            return False
        elif choice == '17':
            print("\nThank you for using Learning Garden. Goodbye!")
            return True
        else:
            print("\nInvalid choice. Please try again.")
            time.sleep(1)

def auth_menu():
    """Show authentication menu"""
    while True:
        print_header("Welcome to Learning Garden")
        print("1. Login")
        print("2. Register")
        print("3. View Subjects (Guest)")
        print("4. View Courses (Guest)")
        print("5. View Leaderboard (Guest)")
        print("6. Exit")
        print()
        
        choice = input("Enter your choice (1-6): ")
        
        if choice == '1':
            if login():
                return True
        elif choice == '2':
            if register():
                return True
        elif choice == '3':
            view_subjects()
        elif choice == '4':
            view_courses()
        elif choice == '5':
            view_leaderboard()
        elif choice == '6':
            print("\nThank you for visiting. Goodbye!")
            return False
        else:
            print("\nInvalid choice. Please try again.")
            time.sleep(1)

if __name__ == "__main__":
    try:
        # Check if already logged in
        if load_token():
            logged_in = True
        else:
            logged_in = auth_menu()
        
        # Main app loop if logged in
        if logged_in:
            exit_app = main_menu()
    except KeyboardInterrupt:
        print("\n\nApplication terminated by user.")
