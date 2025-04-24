from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QGroupBox, QFormLayout, QListWidget, QListWidgetItem,
                            QHeaderView, QSplitter, QFileDialog, QMessageBox,
                            QTabWidget, QTextEdit, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal, QDateTime
from PyQt5.QtGui import QPixmap, QFont, QIcon

class CommunityUI(QWidget):
    # Signal for navigation
    navigate_to_signal = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        
        # Create header
        header_layout = QVBoxLayout()
        title_label = QLabel("Community Support")
        title_label.setFont(QFont("Arial", 24, QFont.Bold))
        title_label.setStyleSheet("color: #07539e;")
        
        # Add divider
        divider = QLabel()
        try:
            pixmap = QPixmap("divider.png")
            divider.setPixmap(pixmap)
        except:
            divider.setText("----------------------------------------------------")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(divider)
        
        # Add header to main layout
        main_layout.addLayout(header_layout)
        
        # Create tabs for different community features
        community_tabs = QTabWidget()
        
        # Discussion forum tab
        forum_tab = QWidget()
        forum_layout = QVBoxLayout()
        
        forum_instructions = QLabel("Connect with other patients and healthcare providers to share experiences, ask questions, and get support.")
        forum_instructions.setWordWrap(True)
        forum_layout.addWidget(forum_instructions)
        
        # Forum topics
        topics_group = QGroupBox("Discussion Topics")
        topics_layout = QVBoxLayout()
        
        topics_list = QListWidget()
        topics_list.setStyleSheet("QListWidget::item { border-bottom: 1px solid #ddd; padding: 10px; }")
        
        topics = [
            "Tips for Daily Exercises - 24 replies",
            "Improving Hand Coordination - 18 replies",
            "Nutrition for Recovery - 32 replies",
            "Managing Frustration During Rehab - 45 replies",
            "Success Stories - 67 replies",
            "Technology Aids for Stroke Recovery - 21 replies"
        ]
        
        for topic in topics:
            topics_list.addItem(topic)
            
        topics_layout.addWidget(topics_list)
        
        # Add new topic button
        new_topic_button = QPushButton("Start New Discussion")
        new_topic_button.setStyleSheet("background-color: #4682B4; color: white;")
        topics_layout.addWidget(new_topic_button)
        
        topics_group.setLayout(topics_layout)
        forum_layout.addWidget(topics_group)
        
        # Selected topic display
        topic_view_group = QGroupBox("Topic: Managing Frustration During Rehab")
        topic_view_layout = QVBoxLayout()
        
        # Create scrollable area for posts
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Sample posts
        posts = [
            {"user": "DrJones", "timestamp": "2023-08-15 14:30", "content": "Frustration is a normal part of the rehabilitation process. Remember that progress is not linear, and it's okay to have both good and bad days.", "is_professional": True},
            {"user": "RecoveryWarrior", "timestamp": "2023-08-15 15:45", "content": "I found that setting smaller, achievable goals helped me manage my frustration. When I focus on small wins, I feel more motivated to continue.", "is_professional": False},
            {"user": "HopeSeeker", "timestamp": "2023-08-16 09:12", "content": "Meditation has been very helpful for me. Just 10 minutes of deep breathing when I feel frustrated has made a huge difference in my outlook.", "is_professional": False},
            {"user": "NurseSmith", "timestamp": "2023-08-16 11:30", "content": "It's also important to communicate with your healthcare team when you're feeling frustrated. We can adjust your rehab plan or provide additional support when needed.", "is_professional": True}
        ]
        
        for post in posts:
            post_box = QGroupBox()
            post_layout = QVBoxLayout()
            
            header_layout = QHBoxLayout()
            
            user_label = QLabel(post["user"])
            user_label.setFont(QFont("Arial", 10, QFont.Bold))
            
            if post["is_professional"]:
                user_label.setStyleSheet("color: #07539e;")
                professional_label = QLabel("Healthcare Professional")
                professional_label.setStyleSheet("color: green; font-style: italic;")
                header_layout.addWidget(user_label)
                header_layout.addWidget(professional_label)
            else:
                header_layout.addWidget(user_label)
            
            header_layout.addStretch()
            
            timestamp_label = QLabel(post["timestamp"])
            timestamp_label.setStyleSheet("color: gray;")
            header_layout.addWidget(timestamp_label)
            
            content_label = QLabel(post["content"])
            content_label.setWordWrap(True)
            content_label.setStyleSheet("background-color: #f0f0f0; padding: 10px; border-radius: 5px;")
            
            post_layout.addLayout(header_layout)
            post_layout.addWidget(content_label)
            
            post_box.setLayout(post_layout)
            scroll_layout.addWidget(post_box)
        
        # Add reply area
        reply_label = QLabel("Your Reply:")
        reply_text = QTextEdit()
        reply_text.setMaximumHeight(100)
        
        post_reply_button = QPushButton("Post Reply")
        post_reply_button.setStyleSheet("background-color: #4682B4; color: white;")
        
        scroll_layout.addWidget(reply_label)
        scroll_layout.addWidget(reply_text)
        scroll_layout.addWidget(post_reply_button)
        
        scroll_area.setWidget(scroll_widget)
        topic_view_layout.addWidget(scroll_area)
        
        topic_view_group.setLayout(topic_view_layout)
        forum_layout.addWidget(topic_view_group)
        
        forum_tab.setLayout(forum_layout)
        
        # Upcoming events tab
        events_tab = QWidget()
        events_layout = QVBoxLayout()
        
        events_instructions = QLabel("Join virtual and local events to connect with others in the neuro-rehabilitation community.")
        events_instructions.setWordWrap(True)
        events_layout.addWidget(events_instructions)
        
        # Events list
        events_list = QListWidget()
        events_list.setStyleSheet("QListWidget::item { border-bottom: 1px solid #ddd; padding: 10px; }")
        
        events = [
            {"title": "Virtual Support Group", "date": "Every Tuesday, 7:00 PM", "type": "Online"},
            {"title": "Recovery Milestones Celebration", "date": "September 10, 2023, 2:00 PM", "type": "Online"},
            {"title": "Guest Speaker: Advances in Neuro-Rehabilitation", "date": "September 17, 2023, 6:30 PM", "type": "Online"},
            {"title": "Local Meetup: Coffee & Conversation", "date": "September 24, 2023, 10:00 AM", "type": "In-person"}
        ]
        
        for event in events:
            item = QListWidgetItem()
            item.setText(f"{event['title']} - {event['date']}")
            
            if event["type"] == "Online":
                item.setIcon(QIcon.fromTheme("network-wireless", QIcon.fromTheme("network-transmit")))
            else:
                item.setIcon(QIcon.fromTheme("user-group", QIcon.fromTheme("stock_people")))
            
            events_list.addItem(item)
            
        events_layout.addWidget(events_list)
        
        # Event details
        event_details_group = QGroupBox("Event Details: Virtual Support Group")
        event_details_layout = QVBoxLayout()
        
        event_description = QLabel("Join our weekly support group to connect with others on their recovery journey. Share your experiences, challenges, and victories in a supportive environment. Healthcare professionals will also be available to answer questions.")
        event_description.setWordWrap(True)
        
        event_details = QLabel("Date: Every Tuesday\nTime: 7:00 PM - 8:30 PM\nLocation: Zoom (link will be provided after registration)")
        
        register_button = QPushButton("Register for Event")
        register_button.setStyleSheet("background-color: #4682B4; color: white;")
        
        event_details_layout.addWidget(event_description)
        event_details_layout.addWidget(event_details)
        event_details_layout.addWidget(register_button)
        
        event_details_group.setLayout(event_details_layout)
        events_layout.addWidget(event_details_group)
        
        events_tab.setLayout(events_layout)
        
        # Resources tab
        resources_tab = QWidget()
        resources_layout = QVBoxLayout()
        
        resources_instructions = QLabel("Access helpful resources for your recovery journey.")
        resources_instructions.setWordWrap(True)
        resources_layout.addWidget(resources_instructions)
        
        # Resources list
        resources_list = QListWidget()
        resources_list.setStyleSheet("QListWidget::item { border-bottom: 1px solid #ddd; padding: 10px; }")
        
        resources = [
            "Educational Articles: Understanding Your Recovery",
            "Video Library: Exercise Demonstrations",
            "Mobile Apps for Rehabilitation",
            "Local Support Services Directory",
            "Nutrition and Diet Guidelines",
            "Mental Health Resources"
        ]
        
        for resource in resources:
            resources_list.addItem(resource)
            
        resources_layout.addWidget(resources_list)
        
        resource_details = QLabel("Select a resource to view details")
        resource_details.setAlignment(Qt.AlignCenter)
        resource_details.setStyleSheet("background-color: #f0f0f0; padding: 20px;")
        resource_details.setMinimumHeight(200)
        
        resources_layout.addWidget(resource_details)
        
        resources_tab.setLayout(resources_layout)
        
        # Add tabs to tab widget
        community_tabs.addTab(forum_tab, "Discussion Forum")
        community_tabs.addTab(events_tab, "Upcoming Events")
        community_tabs.addTab(resources_tab, "Resources")
        
        # Add community tabs to main layout
        main_layout.addWidget(community_tabs)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        # Create buttons for navigation
        sections = ["Home", "Rehab", "Community", "Logout"]
        
        for section in sections:
            button = QPushButton(section)
            button.setStyleSheet("background-color: #4682B4; color: white;")
            # Fix lambda by using a custom slot to avoid closure issues
            button.clicked.connect(self.create_navigation_handler(section))
            nav_layout.addWidget(button)
        
        main_layout.addLayout(nav_layout)
        
        # Set the main layout
        self.setLayout(main_layout) 
        
    def create_navigation_handler(self, section):
        """Create a handler function for navigation buttons to avoid lambda issues"""
        def handler():
            print(f"Navigation button clicked: {section}")
            self.navigate_to_signal.emit(section)
        return handler

    def navigate_to(self, section):
        # Implement the logic to navigate to the specified section
        print(f"Navigating to: {section}")
        # Add the actual implementation here

    def navigate_to_home(self):
        self.navigate_to("Home")

    def navigate_to_rehab(self):
        self.navigate_to("Rehab")

    def navigate_to_community(self):
        self.navigate_to("Community")

    def navigate_to_logout(self):
        self.navigate_to("Logout") 