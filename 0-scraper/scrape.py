from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
import time
import csv
import json
import os
from datetime import datetime
import argparse

def save_conversation(conversation, csv_path):
    """Save or append conversation to the original JSON file"""
    # Get original filename (remove _retry and change to .json)
    base_name = os.path.basename(csv_path)
    original_name = base_name.replace('_retry.csv', '.json')
    json_path = os.path.join('output', original_name)
    
    # Load existing data if file exists
    existing_data = []
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except Exception as e:
            print(f"Error reading existing JSON: {str(e)}")
    
    # Append new conversations
    existing_data.extend(conversation)
    
    # Save back to file
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving JSON: {str(e)}")

def login_to_understand(username, password, csv_path):
    # Setup Chrome driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    
    try:
        # Navigate to the login page
        driver.get("https://app.understand.tech/Login")
        
        # Wait for username field and enter credentials
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-label='📧 Email']"))
        )
        username_field.send_keys(username)
        
        # Find password field and enter password
        password_field = driver.find_element(By.CSS_SELECTOR, "input[aria-label='🔒 Password']")
        password_field.send_keys(password)
        
        # Find and click login button
        login_button = driver.find_element(By.CSS_SELECTOR, "button[kind='primaryFormSubmit']")
        login_button.click()
        
        # Wait for successful login (you might need to adjust this based on the page's behavior)
        WebDriverWait(driver, 10).until(
            EC.url_changes("https://app.understand.tech/Login")
        )
        
        print("Logged in successfully! Waiting 30 seconds...")
        time.sleep(30)
        
        # After successful login, wait for and click the search input
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-autocomplete='list'][role='combobox']"))
        )
        search_input.click()
        search_input.send_keys("CSA Matter SDK Documentation" + Keys.ENTER)
        
        # Wait 7 seconds as requested
        time.sleep(7)
        
        # Read questions from CSV
        with open(csv_path, 'r') as file:
            questions = list(csv.DictReader(file))
        
        # Create output folder if it doesn't exist
        output_folder = 'output'
        os.makedirs(output_folder, exist_ok=True)
        
        # Prepare output file name (same as input but .json)
        base_name = os.path.splitext(os.path.basename(csv_path))[0]
        output_path = os.path.join(output_folder, f"{base_name}.json")
        
        # Store all conversations
        all_conversations = []
        
        # Ask each question from the CSV
        for i, row in enumerate(questions, 1):
            question = row['Query']
            print(f"\nAsking question {i}/{len(questions)}: {question}")
            
            chat_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[aria-label='Submit your prompt for CSA Matter SDK Documentation']"))
            )
            chat_input.send_keys(question + Keys.ENTER)
            
            # Wait for thinking block to appear and disappear
            thinking_selector = "div.st-emotion-cache-j78z8c"
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, thinking_selector))
            )
            print("AI is thinking...")
            WebDriverWait(driver, 60).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, thinking_selector))
            )
            print("AI finished responding")
            
            time.sleep(5)
            
            # Extract latest conversation
            chat_messages = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "stChatMessage"))
            )
            
            # Get the last two messages (question and answer)
            latest_messages = chat_messages[-2:]
            conversation = []
            
            for message in latest_messages:
                is_user = "st-emotion-cache-1c7y2kd" in message.get_attribute("class")
                role = "user" if is_user else "assistant"
                content = message.find_element(By.CSS_SELECTOR, "[data-testid='stMarkdownContainer']").text
                
                conversation.append({
                    "role": role,
                    "content": content
                })
            
            all_conversations.append({
                "trustii_id": row['trustii_id'],
                "conversation": conversation
            })
            
            # Save after each question (in case of crashes)
            save_conversation(all_conversations, csv_path)
        
        print(f"\nAppended conversations to original JSON file")
        return driver, all_conversations
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        driver.quit()
        return None, None

def parse_args():
    parser = argparse.ArgumentParser(description='Scrape conversations from Understand.tech')
    parser.add_argument('--input', '-i', 
                        type=str, 
                        required=True,
                        help='Path to input CSV file containing questions')
    return parser.parse_args()

if __name__ == "__main__":
    # Parse command line arguments
    args = parse_args()
    
    # Validate input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' does not exist!")
        exit(1)
    
    # Run the scraper
    driver, conversations = login_to_understand(
        username="lepageletouquet666@icloud.com",  # hardcode your email
        password="3oot@Root",    # hardcode your password
        csv_path=args.input
    )
