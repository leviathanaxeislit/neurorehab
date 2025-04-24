import os
import re

def fix_navigation_in_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if the file already has the create_navigation_handler method
    if 'def create_navigation_handler' in content:
        print(f"{file_path} already has create_navigation_handler method")
        return False
    
    # Find the pattern for button connections using lambda
    lambda_pattern = r'button\.clicked\.connect\(lambda checked, s=section: self\.navigate_to_signal\.emit\(s\)\)'
    
    # Replace with the fixed version
    fixed_content = re.sub(
        lambda_pattern, 
        'button.clicked.connect(self.create_navigation_handler(section))', 
        content
    )
    
    # Add the create_navigation_handler method before the end of the class
    if fixed_content != content:
        # Find a good place to insert the handler method - right after setLayout(main_layout)
        handler_method = """
    def create_navigation_handler(self, section):
        \"\"\"Create a handler function for navigation buttons to avoid lambda issues\"\"\"
        def handler():
            print(f"Navigation button clicked: {section}")
            self.navigate_to_signal.emit(section)
        return handler
"""
        # Insert before the next method definition or at the end of the file
        pattern = r'(\s+def\s+\w+\s*\()'
        match = re.search(pattern, fixed_content[fixed_content.find('self.setLayout(main_layout)'):])
        
        if match:
            # Insert before the next method
            insert_pos = fixed_content.find('self.setLayout(main_layout)') + len('self.setLayout(main_layout)') + fixed_content[fixed_content.find('self.setLayout(main_layout)'):].find(match.group(1))
            fixed_content = fixed_content[:insert_pos] + handler_method + fixed_content[insert_pos:]
        else:
            # Insert at the end of the file
            fixed_content += handler_method
        
        # Write the fixed content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"Fixed navigation in {file_path}")
        return True
    
    print(f"No changes needed in {file_path}")
    return False

def main():
    # List of UI files to fix
    ui_files = [
        'home_ui.py',
        'physio_ui.py',
        'hand_ui.py',
        'game_ui.py',
        'result_ui.py',
        'rehab_ui.py',
        'community_ui.py',
        'patient_ui.py',
        'snake_game_ui.py',
        'emoji_game_ui.py',
        'ball_game_ui.py'
    ]
    
    # Apply fixes to each file
    fixed_count = 0
    for ui_file in ui_files:
        if os.path.exists(ui_file):
            if fix_navigation_in_file(ui_file):
                fixed_count += 1
        else:
            print(f"File not found: {ui_file}")
    
    print(f"Fixed navigation in {fixed_count} files")

if __name__ == "__main__":
    main() 