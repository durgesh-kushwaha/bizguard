# SETUP — BizGuard

## Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

## Installation

The uploader accepts CSV, TSV, Excel (`.xls`, `.xlsx`), JSON, JSON Lines (`.jsonl`, `.ndjson`), and Parquet business tables. It is available on desktop and mobile browsers. Image and document formats are not transaction tables and are not accepted.

The app uses Pandas by default, including on Streamlit Community Cloud. PySpark is optional and intended for local demonstrations; it is not installed in the Cloud deployment.

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

### Optional: Enable PySpark locally
```bash
pip install -r requirements-spark.txt
java -version
```
PySpark 4.x requires Java 17 or newer. Install a supported JDK if needed, then set `JAVA_HOME` to its installation directory.

### 5. Run the Application
```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`.

## Troubleshooting

### PySpark not finding Java
The app continues to work with Pandas when PySpark or Java is unavailable. For a local Spark demonstration, install the optional requirements and set `JAVA_HOME` to the installed JDK:
```bash
export JAVA_HOME=$(/usr/libexec/java_home -v 17)  # macOS
```

### Port 8501 already in use
```bash
streamlit run app.py --server.port 8502
```

### Module not found errors
Ensure you're running from the project root directory and virtual environment is activated.
