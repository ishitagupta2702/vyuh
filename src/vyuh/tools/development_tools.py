"""
Development Tools for CrewAI Agents
"""

from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import re
import json
import os
from datetime import datetime
import uuid


class FormatterToolInput(BaseModel):
    content: str = Field(description="Content to be formatted")
    format_type: str = Field(description="Type of formatting")


class FormatterTool(BaseTool):
    name: str = "formatter_tool"
    description: str = "Formats content in various formats"
    args_schema: Type[BaseModel] = FormatterToolInput
    
    def _run(self, content: str, format_type: str = "markdown") -> str:
        if format_type.lower() == "markdown":
            return self._format_markdown(content)
        elif format_type.lower() == "json":
            return self._format_json(content)
        else:
            return f"Formatted {format_type} content:\n\n{content}"
    
    def _format_markdown(self, content: str) -> str:
        formatted = content.strip()
        if not formatted.startswith('#'):
            formatted = f"# {formatted.split('\n')[0]}\n\n{formatted}"
        return formatted
    
    def _format_json(self, content: str) -> str:
        try:
            data = json.loads(content)
            return json.dumps(data, indent=2)
        except:
            return content


class ImproverToolInput(BaseModel):
    content: str = Field(description="Content to be improved")
    improvement_type: str = Field(description="Type of improvement")


class ImproverTool(BaseTool):
    name: str = "improver_tool"
    description: str = "Improves content quality and structure"
    args_schema: Type[BaseModel] = ImproverToolInput
    
    def _run(self, content: str, improvement_type: str = "general") -> str:
        if improvement_type.lower() == "code":
            return self._improve_code(content)
        else:
            return self._improve_general(content)
    
    def _improve_code(self, content: str) -> str:
        improved = content
        if "def " in improved and "# " not in improved:
            improved = "# Function to handle the task\n" + improved
        return improved
    
    def _improve_general(self, content: str) -> str:
        improved = content
        improved = re.sub(r'\n\s*\n', '\n\n', improved)
        return improved


class WriteToolInput(BaseModel):
    content: str = Field(description="Content to be written")
    file_type: str = Field(description="Type of file")
    filename: str = Field(description="Name of the file")


class WriteTool(BaseTool):
    name: str = "write_tool"
    description: str = "Writes content to files with proper formatting"
    args_schema: Type[BaseModel] = WriteToolInput
    
    def _run(self, content: str, file_type: str = "text", filename: str = "output") -> str:
        if file_type.lower() == "python":
            return self._write_python_file(content, filename)
        else:
            return self._write_generic_file(content, filename, file_type)
    
    def _write_python_file(self, content: str, filename: str) -> str:
        if not content.startswith('"""') and not content.startswith("'''"):
            content = f'"""\n{filename}\n\n{content}\n"""\n\n'
        return f"# {filename}.py\n{content}"
    
    def _write_generic_file(self, content: str, filename: str, file_type: str) -> str:
        # Don't add extension if filename already has one
        if '.' in filename:
            return f"# {filename}\n{content}"
        else:
            return f"# {filename}.{file_type}\n{content}"


class ReadToolInput(BaseModel):
    content: str = Field(description="Content to be read and analyzed")
    analysis_type: str = Field(description="Type of analysis")


class ReadTool(BaseTool):
    name: str = "read_tool"
    description: str = "Reads and analyzes content for quality and issues"
    args_schema: Type[BaseModel] = ReadToolInput
    
    def _run(self, content: str, analysis_type: str = "general") -> str:
        if analysis_type.lower() == "code":
            return self._analyze_code(content)
        else:
            return self._analyze_general(content)
    
    def _analyze_code(self, content: str) -> str:
        analysis = []
        if "import " in content or "from " in content:
            analysis.append("✅ Has imports")
        else:
            analysis.append("⚠️ Missing imports")
        if "def " in content:
            analysis.append("✅ Has function definitions")
        else:
            analysis.append("⚠️ No function definitions found")
        return f"Code Analysis:\n" + "\n".join(analysis)
    
    def _analyze_general(self, content: str) -> str:
        analysis = []
        char_count = len(content)
        word_count = len(content.split())
        line_count = len(content.split('\n'))
        analysis.append(f"📊 Characters: {char_count}")
        analysis.append(f"📝 Words: {word_count}")
        analysis.append(f"📏 Lines: {line_count}")
        return f"General Analysis:\n" + "\n".join(analysis)


class StorageToolInput(BaseModel):
    content: str = Field(description="Content to be stored")
    agent_name: str = Field(description="Name of the agent that produced this content")
    task_name: str = Field(description="Name of the task that produced this content")
    content_type: str = Field(description="Type of content (code, analysis, documentation, etc.)")
    project_name: str = Field(description="Name of the project")


class StorageTool(BaseTool):
    name: str = "storage_tool"
    description: str = "Stores agent outputs in the resources folder with proper organization"
    args_schema: Type[BaseModel] = StorageToolInput
    
    def _run(self, content: str, agent_name: str, task_name: str, content_type: str = "output", project_name: str = "development_crew") -> str:
        try:
            # Create resources directory if it doesn't exist
            resources_dir = "resources"
            if not os.path.exists(resources_dir):
                os.makedirs(resources_dir)
            
            # Create project directory
            project_dir = os.path.join(resources_dir, project_name)
            if not os.path.exists(project_dir):
                os.makedirs(project_dir)
            
            # Create agent directory
            agent_dir = os.path.join(project_dir, agent_name.replace(" ", "_").lower())
            if not os.path.exists(agent_dir):
                os.makedirs(agent_dir)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            
            # Determine file extension and create professional filename
            if content_type.lower() in ["code", "python", "javascript", "typescript"]:
                extension = "py" if content_type.lower() == "python" else "js" if content_type.lower() == "javascript" else "ts"
            elif content_type.lower() in ["markdown", "documentation", "architecture", "mvp", "requirements"]:
                extension = "md"
            elif content_type.lower() in ["json", "config"]:
                extension = "json"
            else:
                extension = "txt"
            
            # Create professional filename based on content type
            if content_type.lower() in ["architecture", "tech_stack", "system_design"]:
                filename = f"Technical_Architecture_{timestamp}.{extension}"
            elif content_type.lower() in ["mvp", "features", "requirements"]:
                filename = f"Product_Requirements_{timestamp}.{extension}"
            elif content_type.lower() in ["user_stories", "stories"]:
                filename = f"User_Stories_{timestamp}.{extension}"
            else:
                filename = f"{task_name.replace(' ', '_').lower()}_{timestamp}_{unique_id}.{extension}"
            
            filepath = os.path.join(agent_dir, filename)
            
            # Enhance content with professional formatting
            enhanced_content = self._enhance_content(content, agent_name, task_name, content_type, project_name)
            
            # Create metadata
            metadata = {
                "agent_name": agent_name,
                "task_name": task_name,
                "content_type": content_type,
                "project_name": project_name,
                "timestamp": datetime.now().isoformat(),
                "filepath": filepath,
                "content_length": len(enhanced_content),
                "version": "1.0",
                "status": "completed"
            }
            
            # Write enhanced content to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(enhanced_content)
            
            # Create metadata file
            metadata_file = filepath.replace(f".{extension}", "_metadata.json")
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            return f"✅ Content stored successfully!\n📁 File: {filepath}\n📊 Size: {len(enhanced_content)} characters\n🏷️ Type: {content_type}"
            
        except Exception as e:
            return f"❌ Error storing content: {str(e)}"
    
    def _enhance_content(self, content: str, agent_name: str, task_name: str, content_type: str, project_name: str) -> str:
        """Enhance content with professional formatting and structure"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if content_type.lower() in ["architecture", "tech_stack", "system_design"]:
            return self._format_architecture_doc(content, project_name, timestamp)
        elif content_type.lower() in ["mvp", "features", "requirements"]:
            return self._format_mvp_doc(content, project_name, timestamp)
        elif content_type.lower() in ["user_stories", "stories"]:
            return self._format_user_stories_doc(content, project_name, timestamp)
        else:
            return self._format_general_doc(content, agent_name, task_name, project_name, timestamp)
    
    def _format_architecture_doc(self, content: str, project_name: str, timestamp: str) -> str:
        return f"""# Technical Architecture Document
## {project_name}

**Document Type:** Technical Architecture  
**Generated:** {timestamp}  
**Version:** 1.0  
**Status:** Draft

---

## Executive Summary
This document outlines the technical architecture for the {project_name} project, including technology stack, system design, and implementation guidelines.

## Table of Contents
1. [Technology Stack](#technology-stack)
2. [System Architecture](#system-architecture)
3. [Database Design](#database-design)
4. [API Design](#api-design)
5. [Security Considerations](#security-considerations)
6. [Deployment Strategy](#deployment-strategy)
7. [Performance Considerations](#performance-considerations)

---

{content}

---

## Document Information
- **Generated by:** Development Crew AI
- **Last Updated:** {timestamp}
- **Next Review:** TBD
"""
    
    def _format_mvp_doc(self, content: str, project_name: str, timestamp: str) -> str:
        return f"""# Product Requirements Document
## {project_name}

**Document Type:** MVP Requirements  
**Generated:** {timestamp}  
**Version:** 1.0  
**Status:** Draft

---

## Executive Summary
This document defines the Minimum Viable Product (MVP) requirements for the {project_name} project, including core features, user stories, and acceptance criteria.

## Table of Contents
1. [Product Overview](#product-overview)
2. [MVP Features](#mvp-features)
3. [User Stories](#user-stories)
4. [Functional Requirements](#functional-requirements)
5. [Non-Functional Requirements](#non-functional-requirements)
6. [Acceptance Criteria](#acceptance-criteria)
7. [Success Metrics](#success-metrics)

---

{content}

---

## Document Information
- **Generated by:** Development Crew AI
- **Last Updated:** {timestamp}
- **Next Review:** TBD
"""
    
    def _format_user_stories_doc(self, content: str, project_name: str, timestamp: str) -> str:
        return f"""# User Stories Document
## {project_name}

**Document Type:** User Stories  
**Generated:** {timestamp}  
**Version:** 1.0  
**Status:** Draft

---

## Overview
This document contains user stories for the {project_name} project, organized by user roles and feature areas.

## Table of Contents
1. [User Personas](#user-personas)
2. [Epic Stories](#epic-stories)
3. [Feature Stories](#feature-stories)
4. [Acceptance Criteria](#acceptance-criteria)
5. [Story Points](#story-points)

---

{content}

---

## Document Information
- **Generated by:** Development Crew AI
- **Last Updated:** {timestamp}
- **Next Review:** TBD
"""
    
    def _format_general_doc(self, content: str, agent_name: str, task_name: str, project_name: str, timestamp: str) -> str:
        return f"""# {task_name.title()}
## {project_name}

**Document Type:** {agent_name} Output  
**Generated:** {timestamp}  
**Version:** 1.0  
**Status:** Draft

---

## Overview
This document contains the output from the {agent_name} for the task: {task_name}

---

{content}

---

## Document Information
- **Generated by:** Development Crew AI
- **Last Updated:** {timestamp}
- **Next Review:** TBD
"""


class CodeGeneratorToolInput(BaseModel):
    content: str = Field(description="Source code content to be written to file")
    filename: str = Field(description="Name of the file (with extension)")
    file_type: str = Field(description="Type of file (javascript, python, css, html, etc.)")
    project_name: str = Field(description="Name of the project")
    folder_path: str = Field(description="Folder path within the project")
    create_env_files: bool = Field(description="Whether to create environment template files", default=True)


class CodeGeneratorTool(BaseTool):
    name: str = "code_generator_tool"
    description: str = "Creates actual source code files in a proper project structure"
    args_schema: Type[BaseModel] = CodeGeneratorToolInput
    
    def _run(self, content: str, filename: str, file_type: str = "javascript", project_name: str = "app", folder_path: str = "", create_env_files: bool = True) -> str:
        try:
            # Create project directory in current working directory
            project_dir = project_name.replace(" ", "_").lower()
            if not os.path.exists(project_dir):
                os.makedirs(project_dir)
            
            # Create folder structure if specified
            if folder_path:
                # Ensure folder_path doesn't start with / to avoid absolute paths
                folder_path = folder_path.lstrip('/')
                # Handle nested folder paths properly
                path_parts = folder_path.split('/')
                current_path = project_dir
                for part in path_parts:
                    current_path = os.path.join(current_path, part)
                    if not os.path.exists(current_path):
                        os.makedirs(current_path)
                filepath = os.path.join(current_path, filename)
            else:
                filepath = os.path.join(project_dir, filename)
            
            # Clean up the content (remove markdown formatting if present)
            clean_content = self._clean_code_content(content)
            
            # Write the actual source code file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(clean_content)
            
            # Also store in resources for backup
            resources_dir = "resources"
            if not os.path.exists(resources_dir):
                os.makedirs(resources_dir)
            
            backup_dir = os.path.join(resources_dir, project_name, "source_code")
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            backup_filepath = os.path.join(backup_dir, f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_type}")
            with open(backup_filepath, 'w', encoding='utf-8') as f:
                f.write(clean_content)
            
            return f"✅ Source code file created successfully!\n📁 File: {filepath}\n📊 Size: {len(clean_content)} characters\n🏷️ Type: {file_type}\n💾 Backup: {backup_filepath}"
            
        except Exception as e:
            return f"❌ Error creating source code file: {str(e)}"
    
    def _clean_code_content(self, content: str) -> str:
        """Clean up code content by removing markdown formatting and ensuring it's actual code"""
        # If content is just a list of file names, return a warning
        if content.strip().endswith('files') or 'files' in content.lower() and len(content.split()) < 10:
            return f"// ERROR: This file should contain actual code, not just file names\n// Please generate real code content for this file\n\n{content}"
        
        # Remove markdown code blocks
        if "```" in content:
            lines = content.split('\n')
            in_code_block = False
            cleaned_lines = []
            
            for line in lines:
                if line.strip().startswith('```'):
                    in_code_block = not in_code_block
                    continue
                if in_code_block:
                    cleaned_lines.append(line)
                elif not line.strip().startswith('//') and not line.strip().startswith('#'):
                    cleaned_lines.append(line)
            
            result = '\n'.join(cleaned_lines)
            
            # If result is too short or just contains file names, return a template
            if len(result.strip()) < 50:
                return self._generate_code_template(content)
            
            return result
        else:
            # If content doesn't look like code, generate a template
            if len(content.strip()) < 100 and ('file' in content.lower() or 'folder' in content.lower()):
                return self._generate_code_template(content)
            return content
    
    def _generate_code_template(self, content: str) -> str:
        """Generate a basic code template based on the filename"""
        if 'server.js' in content.lower():
            return """const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const dotenv = require('dotenv');

dotenv.config();

const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Database connection
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/photographer_social', {
  useNewUrlParser: true,
  useUnifiedTopology: true
});

// Routes
app.use('/api/users', require('./routes/users'));
app.use('/api/photos', require('./routes/photos'));

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});"""
        elif 'package.json' in content.lower():
            return """{
  "name": "photographer-social-backend",
  "version": "1.0.0",
  "description": "Backend API for photographer social media platform",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "mongoose": "^7.5.0",
    "cors": "^2.8.5",
    "dotenv": "^16.3.1",
    "bcryptjs": "^2.4.3",
    "jsonwebtoken": "^9.0.2",
    "multer": "^1.4.5-lts.1"
  },
  "devDependencies": {
    "nodemon": "^3.0.1"
  }
}"""
        elif 'auth.js' in content.lower():
            return """const jwt = require('jsonwebtoken');

const auth = (req, res, next) => {
  try {
    const token = req.header('Authorization').replace('Bearer ', '');
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded;
    next();
  } catch (error) {
    res.status(401).json({ message: 'Authentication failed' });
  }
};

module.exports = auth;"""
        elif 'user.js' in content.lower():
            return """const mongoose = require('mongoose');

const userSchema = new mongoose.Schema({
  username: { type: String, required: true, unique: true },
  email: { type: String, required: true, unique: true },
  password: { type: String, required: true },
  bio: String,
  profileImage: String,
  followers: [{ type: mongoose.Schema.Types.ObjectId, ref: 'User' }],
  following: [{ type: mongoose.Schema.Types.ObjectId, ref: 'User' }],
  createdAt: { type: Date, default: Date.now }
});

module.exports = mongoose.model('User', userSchema);"""
        elif 'App.js' in content.lower():
            return """import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import './App.css';

function App() {
  return (
    <div className="App">
      <Router>
        <Switch>
          <Route exact path="/" component={Home} />
          <Route path="/upload" component={PhotoUpload} />
          <Route path="/profile" component={Profile} />
          <Route path="/feed" component={Feed} />
        </Switch>
      </Router>
    </div>
  );
}

export default App;"""
        else:
            return f"// TODO: Implement {content}\n// This file should contain actual code implementation\n\n{content}"


class ProjectSetupToolInput(BaseModel):
    project_name: str = Field(description="Name of the project")
    project_type: str = Field(description="Type of project (fullstack, frontend, backend)")
    tech_stack: str = Field(description="Technology stack used")


class ProjectSetupTool(BaseTool):
    name: str = "project_setup_tool"
    description: str = "Creates project setup files like README.md, package.json, and environment templates"
    args_schema: Type[BaseModel] = ProjectSetupToolInput
    
    def _run(self, project_name: str, project_type: str = "fullstack", tech_stack: str = "React, Node.js, MongoDB") -> str:
        try:
            project_dir = project_name.replace(" ", "_").lower()
            
            # Create README.md
            readme_content = self._generate_readme(project_name, project_type, tech_stack)
            readme_path = os.path.join(project_dir, "README.md")
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            # Create .env.example for backend
            if "backend" in project_type.lower() or "fullstack" in project_type.lower():
                env_content = self._generate_env_example()
                env_path = os.path.join(project_dir, "src/server/.env.example")
                os.makedirs(os.path.dirname(env_path), exist_ok=True)
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.write(env_content)
            
            # Create package.json for backend
            if "backend" in project_type.lower() or "fullstack" in project_type.lower():
                package_content = self._generate_backend_package()
                package_path = os.path.join(project_dir, "src/server/package.json")
                with open(package_path, 'w', encoding='utf-8') as f:
                    f.write(package_content)
            
            # Create package.json for frontend
            if "frontend" in project_type.lower() or "fullstack" in project_type.lower():
                frontend_package_content = self._generate_frontend_package()
                frontend_package_path = os.path.join(project_dir, "src/client/package.json")
                with open(frontend_package_path, 'w', encoding='utf-8') as f:
                    f.write(frontend_package_content)
            
            return f"✅ Project setup files created successfully!\n📁 README.md: {readme_path}\n📁 Environment files and package.json files created"
            
        except Exception as e:
            return f"❌ Error creating project setup files: {str(e)}"
    
    def _generate_readme(self, project_name: str, project_type: str, tech_stack: str) -> str:
        return f"""# {project_name}

A {project_type} application built with {tech_stack}.

## 🚀 Quick Start

### Prerequisites
- Node.js (v14 or higher)
- npm or yarn
- MongoDB (local or MongoDB Atlas)

### Backend Setup
```bash
cd src/server
npm install
cp .env.example .env
# Edit .env with your API keys
npm start
```

### Frontend Setup
```bash
cd src/client
npm install
npm start
```

## 🔑 Required API Keys

### Free Services Available:
- **MongoDB Atlas**: [Sign up here](https://mongodb.com) (Free tier: 512MB)
- **Stripe**: [Sign up here](https://stripe.com) (Free to start, pay per transaction)
- **JWT Secret**: Generate a random string for authentication

### Environment Variables:
Copy `.env.example` to `.env` and fill in your keys:
```bash
MONGODB_URI=mongodb://localhost:27017/your_database_name
JWT_SECRET=your_jwt_secret_key_here
STRIPE_SECRET_KEY=sk_test_your_stripe_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_key_here
```

## 📁 Project Structure
```
{project_name}/
├── src/
│   ├── server/          # Backend (Node.js/Express)
│   └── client/          # Frontend (React)
├── README.md
└── .env.example
```

## 🚀 Deployment
- **Backend**: Deploy to Heroku, Railway, or Render
- **Frontend**: Deploy to Vercel, Netlify, or GitHub Pages
- **Database**: Use MongoDB Atlas (free tier available)

## 📝 License
MIT
"""
    
    def _generate_env_example(self) -> str:
        return """# Environment Variables
# Copy this file to .env and fill in your actual values

# Database
MONGODB_URI=mongodb://localhost:27017/your_database_name
# Or use MongoDB Atlas: mongodb+srv://username:password@cluster.mongodb.net/database

# Authentication
JWT_SECRET=your_jwt_secret_key_here
# Generate a random string: node -e "console.log(require('crypto').randomBytes(64).toString('hex'))"

# Payment Processing (Stripe)
STRIPE_SECRET_KEY=sk_test_your_stripe_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_key_here
# Get your keys from: https://dashboard.stripe.com/apikeys

# Server Configuration
PORT=5000
NODE_ENV=development

# Optional: Email Service (SendGrid, Mailgun, etc.)
EMAIL_SERVICE_API_KEY=your_email_service_key_here
"""
    
    def _generate_backend_package(self) -> str:
        return """{
  "name": "backend",
  "version": "1.0.0",
  "description": "Backend API server",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js",
    "test": "jest"
  },
  "dependencies": {
    "express": "^4.18.2",
    "mongoose": "^7.5.0",
    "cors": "^2.8.5",
    "jsonwebtoken": "^9.0.2",
    "bcryptjs": "^2.4.3",
    "dotenv": "^16.3.1",
    "stripe": "^13.5.0",
    "express-validator": "^7.0.1"
  },
  "devDependencies": {
    "nodemon": "^3.0.1",
    "jest": "^29.6.2"
  },
  "keywords": ["api", "backend", "express", "mongodb"],
  "author": "",
  "license": "MIT"
}"""
    
    def _generate_frontend_package(self) -> str:
        return """{
  "name": "frontend",
  "version": "1.0.0",
  "description": "Frontend React application",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.15.0",
    "axios": "^1.5.0",
    "@stripe/stripe-js": "^2.1.0",
    "react-stripe-js": "^2.1.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^5.17.0",
    "@testing-library/react": "^13.4.0",
    "@testing-library/user-event": "^14.4.3",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}"""


class ZipGeneratorToolInput(BaseModel):
    project_name: str = Field(description="Name of the project to zip")
    include_resources: bool = Field(description="Whether to include resources folder in zip", default=False)


class ZipGeneratorTool(BaseTool):
    name: str = "zip_generator_tool"
    description: str = "Creates a zip file of the generated project for easy download"
    args_schema: Type[BaseModel] = ZipGeneratorToolInput
    
    def _run(self, project_name: str, include_resources: bool = False) -> str:
        try:
            import zipfile
            from datetime import datetime
            
            project_dir = project_name.replace(" ", "_").lower()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"{project_name}_{timestamp}.zip"
            
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add project files
                for root, dirs, files in os.walk(project_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, project_dir)
                        zipf.write(file_path, arcname)
                
                # Optionally add resources folder
                if include_resources:
                    resources_dir = "resources"
                    if os.path.exists(resources_dir):
                        for root, dirs, files in os.walk(resources_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, ".")
                                zipf.write(file_path, arcname)
            
            return f"✅ Project zip file created successfully!\n📦 File: {zip_filename}\n📊 Size: {os.path.getsize(zip_filename)} bytes\n📁 Project: {project_dir}"
            
        except Exception as e:
            return f"❌ Error creating zip file: {str(e)}"


# Create tool instances
formatter_tool = FormatterTool()
improver_tool = ImproverTool()
write_tool = WriteTool()
read_tool = ReadTool()
storage_tool = StorageTool()
code_generator_tool = CodeGeneratorTool()
project_setup_tool = ProjectSetupTool()
zip_generator_tool = ZipGeneratorTool()

# Export tools
__all__ = [
    "formatter_tool",
    "improver_tool", 
    "write_tool",
    "read_tool",
    "storage_tool",
    "code_generator_tool",
    "project_setup_tool",
    "zip_generator_tool"
]
