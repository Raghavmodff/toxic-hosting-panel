import os
import sys
import ast
import subprocess
import signal
from threading import Thread
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse

app = FastAPI(title="Toxic Hosting Engine - Live Terminal")

UPLOAD_DIR = "hosted_apps"
LOG_DIR = "logs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

RUNNING_PROCESSES = {}
SCRIPT_STATUS = {}  # "installing", "running", "stopped"

# Common Import -> PyPI Package Mapping
PACKAGE_MAP = {
    "telebot": "pyTelegramBotAPI",
    "PIL": "Pillow",
    "cv2": "opencv-python",
    "bs4": "beautifulsoup4",
    "fitz": "PyMuPDF",
    "yaml": "PyYAML",
    "crypto": "pycryptodome",
    "telegram": "python-telegram-bot",
}

def auto_install_and_run(filename, filepath, log_path):
    """Real-time terminal output streaming directly to console logs"""
    SCRIPT_STATUS[filename] = "installing"
    
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"\n==================================================\n")
        log_file.write(f"🔍 [AUTO-INSTALLER] Scanning dependencies for {filename}...\n")
        log_file.flush()

        # 1. AST Parsing to find imported libraries
        detected_imports = set()
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                tree = ast.parse(f.read(), filename=filepath)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            detected_imports.add(alias.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            detected_imports.add(node.module.split('.')[0])
        except Exception as e:
            log_file.write(f"⚠️ [AST ERROR] Syntax error in file: {e}\n")
            log_file.flush()

        stdlib = getattr(sys, "stdlib_module_names", set())
        packages_to_install = []

        for mod in detected_imports:
            if mod in stdlib or mod in sys.builtin_module_names:
                continue
            pypi_name = PACKAGE_MAP.get(mod, mod)
            packages_to_install.append(pypi_name)

        # 2. Run PIP Install in Real-Time if packages detected
        if packages_to_install:
            log_file.write(f"📦 Found missing packages: {', '.join(packages_to_install)}\n")
            log_file.write(f"⚡ Launching Live PIP Installation...\n")
            log_file.write(f"--------------------------------------------------\n")
            log_file.flush()

            cmd = [sys.executable, "-u", "-m", "pip", "install"] + packages_to_install
            
            # Live Terminal Output Stream
            pip_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Write line-by-line instantly to log file
            for line in pip_proc.stdout:
                log_file.write(line)
                log_file.flush()

            pip_proc.wait()

            log_file.write(f"--------------------------------------------------\n")
            log_file.write(f"✅ All dependencies installed successfully!\n")
            log_file.flush()
        else:
            log_file.write(f"✅ All required libraries are already installed.\n")
            log_file.flush()

        log_file.write(f"🚀 Starting Script Execution: python3 {filename}\n")
        log_file.write(f"==================================================\n\n")
        log_file.flush()

        # 3. Start Main Python Script
        proc = subprocess.Popen(
            [sys.executable, "-u", filepath],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid
        )
        RUNNING_PROCESSES[filename] = proc
        SCRIPT_STATUS[filename] = "running"

@app.post("/upload")
async def upload_script(file: UploadFile = File(...)):
    if not file.filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="Only .py files allowed!")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return {"status": "success", "message": f"{file.filename} uploaded!"}

@app.get("/list")
def list_scripts():
    files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith(".py")]
    result = []
    for filename in files:
        status = SCRIPT_STATUS.get(filename, "stopped")
        pid = None
        
        if filename in RUNNING_PROCESSES:
            proc = RUNNING_PROCESSES[filename]
            if proc.poll() is None:
                pid = proc.pid
            else:
                del RUNNING_PROCESSES[filename]
                SCRIPT_STATUS[filename] = "stopped"
                status = "stopped"

        result.append({
            "filename": filename,
            "status": status,
            "pid": pid
        })
    return result

@app.post("/start/{filename}")
def start_script(filename: str):
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found!")
    
    if filename in RUNNING_PROCESSES and RUNNING_PROCESSES[filename].poll() is None:
        return {"status": "warning", "message": "Script is already running!"}

    log_path = os.path.join(LOG_DIR, f"{filename}.log")
    
    # Run installation & script in background thread so UI doesn't freeze
    Thread(target=auto_install_and_run, args=(filename, filepath, log_path), daemon=True).start()
    
    return {"status": "success", "message": "Installation & Execution started!"}

@app.post("/stop/{filename}")
def stop_script(filename: str):
    if filename in RUNNING_PROCESSES:
        proc = RUNNING_PROCESSES[filename]
        if proc.poll() is None:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            del RUNNING_PROCESSES[filename]
            SCRIPT_STATUS[filename] = "stopped"
            return {"status": "success", "message": "Script stopped!"}
    SCRIPT_STATUS[filename] = "stopped"
    return {"status": "error", "message": "Script is not running!"}

@app.get("/logs/{filename}")
def get_logs(filename: str):
    log_path = os.path.join(LOG_DIR, f"{filename}.log")
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            return {"logs": "".join(lines[-200:])}
    return {"logs": "No logs available."}

@app.get("/", response_class=HTMLResponse)
def dashboard():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TOXIC HOSTING PANEL</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-950 text-white font-sans p-6">
        <div class="max-w-4xl mx-auto">
            <h1 class="text-3xl font-bold mb-6 text-yellow-400">⚡ TOXIC HOSTING ENGINE</h1>
            
            <div class="bg-gray-900 p-4 rounded-lg mb-6 border border-gray-800">
                <h2 class="text-lg font-semibold mb-3 text-gray-300">Upload Script</h2>
                <div class="flex gap-4">
                    <input type="file" id="fileInput" accept=".py" class="bg-gray-800 text-sm rounded p-2 w-full text-gray-300">
                    <button onclick="uploadFile()" class="bg-yellow-500 hover:bg-yellow-600 font-bold px-6 py-2 rounded text-black">Upload</button>
                </div>
            </div>

            <div class="bg-gray-900 p-4 rounded-lg mb-6 border border-gray-800">
                <h2 class="text-lg font-semibold mb-3 text-gray-300">Active Scripts</h2>
                <div id="scriptList" class="space-y-3">Loading...</div>
            </div>

            <div class="bg-gray-900 p-4 rounded-lg border border-gray-800">
                <div class="flex justify-between items-center mb-2">
                    <h2 class="text-lg font-semibold text-gray-300">Live Console Log (<span id="activeLogFile" class="text-yellow-400">Select Script</span>)</h2>
                    <button onclick="refreshLogs()" class="bg-gray-800 hover:bg-gray-700 text-xs px-3 py-1 rounded">Refresh</button>
                </div>
                <pre id="logOutput" class="bg-black p-4 rounded text-green-400 text-xs h-80 overflow-y-auto font-mono border border-gray-800">Select "Logs" to view real-time installation and output...</pre>
            </div>
        </div>

        <script>
            let currentLogScript = null;

            async function fetchScripts() {
                const res = await fetch('/list');
                const data = await res.json();
                const container = document.getElementById('scriptList');
                container.innerHTML = '';

                data.forEach(item => {
                    const div = document.createElement('div');
                    div.className = 'flex justify-between items-center bg-gray-800 p-3 rounded';
                    
                    let statusBadge = '<span class="bg-red-500 text-white text-xs px-2 py-1 rounded">STOPPED</span>';
                    if (item.status === 'installing') {
                        statusBadge = '<span class="bg-yellow-500 text-black font-bold text-xs px-2 py-1 rounded animate-pulse">INSTALLING PIP...</span>';
                    } else if (item.status === 'running') {
                        statusBadge = `<span class="bg-green-500 text-black font-bold text-xs px-2 py-1 rounded">RUNNING (PID: ${item.pid})</span>`;
                    }

                    div.innerHTML = `
                        <div class="flex items-center gap-3">
                            <span class="font-mono text-sm">${item.filename}</span>
                            ${statusBadge}
                        </div>
                        <div class="flex gap-2">
                            ${item.status === 'running' 
                                ? `<button onclick="stopScript('${item.filename}')" class="bg-red-600 text-xs px-3 py-1 rounded">Stop</button>`
                                : `<button onclick="startScript('${item.filename}')" class="bg-green-600 text-xs px-3 py-1 rounded">Start</button>`
                            }
                            <button onclick="viewLogs('${item.filename}')" class="bg-blue-600 text-xs px-3 py-1 rounded">Logs</button>
                        </div>
                    `;
                    container.appendChild(div);
                });
            }

            async function uploadFile() {
                const fileInput = document.getElementById('fileInput');
                if(!fileInput.files[0]) return alert("Select file first!");
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                await fetch('/upload', { method: 'POST', body: formData });
                fileInput.value = '';
                fetchScripts();
            }

            async function startScript(filename) {
                viewLogs(filename);
                await fetch(`/start/${filename}`, { method: 'POST' });
                fetchScripts();
            }

            async function stopScript(filename) {
                await fetch(`/stop/${filename}`, { method: 'POST' });
                fetchScripts();
            }

            function viewLogs(filename) {
                currentLogScript = filename;
                document.getElementById('activeLogFile').innerText = filename;
                refreshLogs();
            }

            async function refreshLogs() {
                if(!currentLogScript) return;
                const res = await fetch(`/logs/${currentLogScript}`);
                const data = await res.json();
                const logBox = document.getElementById('logOutput');
                logBox.innerText = data.logs;
                logBox.scrollTop = logBox.scrollHeight;
            }

            fetchScripts();
            setInterval(() => {
                fetchScripts();
                if(currentLogScript) refreshLogs();
            }, 2000); // Live terminal update every 2 seconds
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
