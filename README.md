# Chatbot for Fast Document Reading

A dashboard application that enables employees to read documents quickly using a GPT-powered chatbot. The application is built with HTML, CSS, and JavaScript, utilizing the Bootstrap framework for responsive design.

## Features

### Document Organization

- **Document Groups**: Organize documents into categories (Compliance, Risk, Operations, etc.)
- **Group Management**: Add, rename, and delete document groups
- **Alphabetical Sorting**: Groups are automatically sorted alphabetically

### Document Management

- **File Support**: Upload and manage PDF, DOCX, and XLSX files
- **Link Management**: Add and organize external links
- **Selection**: Select multiple documents using checkboxes
- **Context Menu**: Right-click to rename or delete items

### Chat Interface

- **Interactive Chat**: Communicate with the GPT-powered chatbot
- **Document Context**: Ask questions about selected documents
- **Fast Responses**: Get quick answers to document-related queries

## Setup Instructions

1. Clone the repository
2. Open `index.html` in a web browser

## Usage Guide

### Managing Document Groups

1. Click the '+' button next to "Document Groups" to add a new group
2. Right-click on a group to rename or delete it
3. Click on a group to view its contents in the right sidebar

### Managing Files

1. Select a document group
2. Click the upload button to add files (PDF, DOCX, XLSX only)
3. Right-click on a file to rename or delete it
4. Use checkboxes to select files for the chatbot to analyze

### Managing Links

1. Select a document group
2. Click the '+' button to add a new link
3. Enter the link name and URL
4. Right-click on a link to rename or delete it

### Using the Chatbot

1. Select documents you want to discuss
2. Type your question in the chat input
3. Press Enter or click the Send button
4. View the chatbot's response in the chat window

## Technical Details

- **Frontend**: HTML5, CSS3, JavaScript
- **Framework**: Bootstrap 5
- **Icons**: Font Awesome
- **Responsive Design**: Optimized for desktop and mobile devices

## Note

This is a frontend prototype. In a production environment, you would need to:

1. Implement backend services for document storage and retrieval
2. Integrate with a GPT API for the chatbot functionality
3. Add user authentication and access control
4. Implement document parsing and analysis features
