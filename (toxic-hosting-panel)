import os
import subprocess
import signal
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse

app = FastAPI(title="TOXIC HOSTING PANEL")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "hosted_apps")
LOG_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

RUNNING_PROCESSES = {}

@app.post("/upload")
async def upload_script(file: UploadFile = File(...)):
    if not file.filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="Sirf .py files allow hain!")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return {"status": "success", "message": f"{file.filename} uploaded successfully!"}

@app.get("/list")
def list_scripts():
    files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith(".py")]
    result = []
    for filename in files:
        is_running = False
        pid = None
        if filename in RUNNING_PROCESSES:
            proc = RUNNING_PROCESSES[filename]
            if proc.poll() is None:
                is_running = True
                pid = proc.pid
            else:
                del RUNNING_PROCESSES[filename]
        
        result.append({
            "filename": filename,
            "running": is_running,
            "pid": pid
        })
    return result

@app.post("/start/{filename}")
def start_script(filename: str):
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File nahi mili!")
    
    if filename in RUNNING_PROCESSES and RUNNING_PROCESSES[filename].poll() is None:
        return {"status": "warning", "message": "Script pehle se run ho rahi hai!"}

    log_path = os.path.join(LOG_DIR, f"{filename}.log")
    log_file = open(log_path, "a", buffering=1)

    proc = subprocess.Popen(
        ["python3", "-u", filepath],
        stdout=log_file,
        stderr=subprocess.STDOUT,
        cwd=UPLOAD_DIR,
        preexec_fn=os.setsid if hasattr(os, "setsid") else None
    )
    RUNNING_PROCESSES[filename] = proc
    return {"status": "success", "message": f"Script started with PID {proc.pid}"}

@app.post("/stop/{filename}")
def stop_script(filename: str):
    if filename in RUNNING_PROCESSES:
        proc = RUNNING_PROCESSES[filename]
        if proc.poll() is None:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except Exception:
                proc.terminate()
            del RUNNING_PROCESSES[filename]
            return {"status": "success", "message": "Script stopped!"}
    return {"status": "error", "message": "Script run nahi ho rahi hai!"}

@app.get("/logs/{filename}")
def get_logs(filename: str):
    log_path = os.path.join(LOG_DIR, f"{filename}.log")
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            return {"logs": "".join(lines[-200:])}
    return {"logs": "Logs file create nahi hui abhi tak."}

@app.get("/", response_class=HTMLResponse)
def dashboard():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TOXIC HOSTING PANEL ☣️</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            @keyframes pulse-glow {
                0%, 100% { box-shadow: 0 0 15px rgba(234, 179, 8, 0.4); }
                50% { box-shadow: 0 0 30px rgba(234, 179, 8, 0.8); }
            }
            .toxic-glow { animation: pulse-glow 2.5s infinite; }
            .fade-out { opacity: 0; visibility: hidden; transition: opacity 0.6s ease, visibility 0.6s; }
        </style>
    </head>
    <body class="bg-gray-950 text-gray-100 font-sans min-h-screen flex flex-col justify-between">

        <div id="splashScreen" class="fixed inset-0 bg-black z-50 flex flex-col items-center justify-center p-4">
            <div class="text-center space-y-4">
                <div class="inline-block p-4 rounded-full bg-yellow-500/10 border-2 border-yellow-500/50 toxic-glow mb-2">
                    <i class="fa-solid fa-biohazard text-6xl text-yellow-400 animate-spin" style="animation-duration: 8s;"></i>
                </div>
                <h1 class="text-3xl md:text-5xl font-extrabold tracking-wider text-yellow-400 uppercase">
                    TOXIC HOSTING
                </h1>
                <p class="text-xs text-gray-400 font-mono tracking-widest">INITIALIZING VIRTUAL ENVIRONMENT...</p>
                
                <div class="w-64 md:w-80 bg-gray-800 h-2 rounded-full overflow-hidden border border-gray-700 mx-auto mt-4">
                    <div id="progressBar" class="bg-gradient-to-r from-yellow-500 to-green-500 h-full w-0 transition-all duration-300"></div>
                </div>
                <p id="splashStatus" class="text-xs text-yellow-500/80 font-mono">Loading Modules...</p>
            </div>
        </div>

        <div id="mainApp" class="opacity-0 transition-opacity duration-700">
            <header class="bg-gray-900/80 backdrop-blur border-b border-yellow-500/20 px-4 py-3 sticky top-0 z-40">
                <div class="max-w-4xl mx-auto flex justify-between items-center">
                    <div class="flex items-center gap-3">
                        <i class="fa-solid fa-biohazard text-yellow-400 text-2xl"></i>
                        <div>
                            <h1 class="text-lg font-bold text-yellow-400 leading-none">TOXIC HOSTING</h1>
                            <span class="text-[10px] text-gray-400 tracking-wider">PYTHON PROCESS ENGINE</span>
                        </div>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="inline-flex items-center px-2 py-1 rounded text-xs font-mono bg-green-500/10 text-green-400 border border-green-500/30">
                            <span class="w-2 h-2 rounded-full bg-green-400 mr-1.5 animate-ping"></span> ONLINE 24/7
                        </span>
                    </div>
                </div>
            </header>

            <main class="max-w-4xl mx-auto p-4 space-y-4">
                <div class="bg-gray-900 p-4 rounded-xl border border-gray-800 shadow-lg">
                    <h2 class="text-sm font-semibold mb-3 text-gray-300 flex items-center gap-2">
                        <i class="fa-solid fa-cloud-arrow-up text-yellow-400"></i> Deploy New Script
                    </h2>
                    <div class="flex flex-col sm:flex-row gap-2">
                        <input type="file" id="fileInput" accept=".py" class="bg-gray-800 text-xs text-gray-300 rounded-lg p-2.5 border border-gray-700 w-full focus:outline-none focus:border-yellow-500">
                        <button onclick="uploadFile()" class="bg-yellow-500 hover:bg-yellow-400 text-black font-bold px-6 py-2.5 rounded-lg text-xs tracking-wider transition-all flex items-center justify-center gap-2">
                            <i class="fa-solid fa-upload"></i> UPLOAD
                        </button>
                    </div>
                </div>

                <div class="bg-gray-900 p-4 rounded-xl border border-gray-800 shadow-lg">
                    <h2 class="text-sm font-semibold mb-3 text-gray-300 flex items-center justify-between">
                        <span class="flex items-center gap-2"><i class="fa-solid fa-server text-yellow-400"></i> Active Containers</span>
                        <button onclick="fetchScripts()" class="text-xs text-gray-400 hover:text-yellow-400"><i class="fa-solid fa-rotate"></i></button>
                    </h2>
                    <div id="scriptList" class="space-y-2">
                        <div class="text-center py-4 text-gray-500 text-xs">Loading containers...</div>
                    </div>
                </div>

                <div class="bg-gray-900 p-4 rounded-xl border border-gray-800 shadow-lg">
                    <div class="flex justify-between items-center mb-3">
                        <h2 class="text-sm font-semibold text-gray-300 flex items-center gap-2">
                            <i class="fa-solid fa-terminal text-yellow-400"></i> Console Logs: 
                            <span id="activeLogFile" class="text-yellow-400 font-mono">None Selected</span>
                        </h2>
                        <button onclick="refreshLogs()" class="bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-300 text-xs px-3 py-1.5 rounded-lg flex items-center gap-1.5">
                            <i class="fa-solid fa-arrows-rotate"></i> Refresh
                        </button>
                    </div>
                    <pre id="logOutput" class="bg-black/90 border border-gray-800 p-3.5 rounded-lg text-green-400 text-xs h-64 overflow-y-auto font-mono leading-relaxed select-text">Click "Logs" on any running script to view terminal output...</pre>
                </div>
            </main>
        </div>

        <footer class="text-center py-4 text-xs text-gray-600 border-t border-gray-900 mt-6">
            TOXIC HOSTING PANEL &bull; Cloud VPS Engine
        </footer>

        <script>
            window.addEventListener('DOMContentLoaded', () => {
                const splash = document.getElementById('splashScreen');
                const mainApp = document.getElementById('mainApp');
                const pBar = document.getElementById('progressBar');
                const pStatus = document.getElementById('splashStatus');

                const steps = [
                    { progress: '25%', status: 'Loading System Libraries...' },
                    { progress: '50%', status: 'Checking Background Processes...' },
                    { progress: '85%', status: 'Connecting Engine Ports...' },
                    { progress: '100%', status: 'System Ready!' }
                ];

                let idx = 0;
                const interval = setInterval(() => {
                    if (idx < steps.length) {
                        pBar.style.width = steps[idx].progress;
                        pStatus.innerText = steps[idx].status;
                        idx++;
                    } else {
                        clearInterval(interval);
                        setTimeout(() => {
                            splash.classList.add('fade-out');
                            mainApp.classList.remove('opacity-0');
                            setTimeout(() => splash.remove(), 600);
                        }, 400);
                    }
                }, 300);
            });

            let currentLogScript = null;

            async function fetchScripts() {
                try {
                    const res = await fetch('/list');
                    const data = await res.json();
                    const container = document.getElementById('scriptList');
                    container.innerHTML = '';

                    if (data.length === 0) {
                        container.innerHTML = '<p class="text-gray-500 text-xs text-center py-3">No Python scripts deployed yet.</p>';
                        return;
                    }

                    data.forEach(item => {
                        const div = document.createElement('div');
                        div.className = 'flex flex-col sm:flex-row sm:items-center justify-between bg-gray-800/60 border border-gray-700/50 p-3 rounded-lg gap-2';
                        
                        const statusBadge = item.running 
                            ? `<span class="bg-green-500/20 text-green-400 border border-green-500/30 text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span> RUNNING (${item.pid})</span>`
                            : `<span class="bg-red-500/20 text-red-400 border border-red-500/30 text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-red-400"></span> STOPPED</span>`;

                        div.innerHTML = `
                            <div class="flex items-center gap-2">
                                <i class="fa-brands fa-python text-yellow-400 text-lg"></i>
                                <span class="font-mono text-sm text-gray-200 font-semibold">${item.filename}</span>
                                ${statusBadge}
                            </div>
                            <div class="flex items-center gap-2">
                                ${item.running 
                                    ? `<button onclick="stopScript('${item.filename}')" class="bg-red-600/80 hover:bg-red-600 text-white text-xs px-3 py-1.5 rounded-md font-medium transition-colors">Stop</button>`
                                    : `<button onclick="startScript('${item.filename}')" class="bg-green-600/80 hover:bg-green-600 text-white text-xs px-3 py-1.5 rounded-md font-medium transition-colors">Start</button>`
                                }
                                <button onclick="viewLogs('${item.filename}')" class="bg-blue-600/80 hover:bg-blue-600 text-white text-xs px-3 py-1.5 rounded-md font-medium transition-colors">Logs</button>
                            </div>
                        `;
                        container.appendChild(div);
                    });
                } catch (e) {
                    console.error("Fetch Error:", e);
                }
            }

            async function uploadFile() {
                const fileInput = document.getElementById('fileInput');
                if(!fileInput.files[0]) return alert("Pehle file choose karo!");
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                await fetch('/upload', { method: 'POST', body: formData });
                fileInput.value = '';
                fetchScripts();
            }

            async function startScript(filename) {
                await fetch(`/start/${filename}`, { method: 'POST' });
                viewLogs(filename);
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
            setInterval(fetchScripts, 5000);
            setInterval(refreshLogs, 2500);
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("hosting_panel:app", host="0.0.0.0", port=port)
