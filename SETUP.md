# SETUP — BizGuard

## Prerequisites
- Python 3.9 or higher
- Java 8 or 11 (required for PySpark)
- pip (Python package manager)

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd BizGuard
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Verify Java (for PySpark)
```bash
java -version
```
PySpark requires Java 8 or 11. If not installed:
- **macOS:** `brew install openjdk@11`
- **Ubuntu:** `sudo apt install openjdk-11-jdk`
- **Windows:** Download from adoptium.net

### 5. Run the Application
```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`.

## Troubleshooting

### PySpark not finding Java
Set JAVA_HOME environment variable:
```bash
export JAVA_HOME=$(/usr/libexec/java_home)  # macOS
```

### Port 8501 already in use
```bash
streamlit run app.py --server.port 8502
```

### Module not found errors
Ensure you're running from the project root directory and virtual environment is activated.
