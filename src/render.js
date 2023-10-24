const { remote } = require('electron');
const { dialog } = remote;
const { spawn, exec } = require('child_process');
const path = require('path');

// Initialize application
async function initializeApp() {
    await printPythonExecutablePath();
    setupOpenFileButton();
}

// Prints the Python executable used by Electron
async function printPythonExecutablePath() {
    exec('python -u -c "import sys; print(sys.executable)"', (error, stdout) => {
        if (error) {
            console.error(`Python Error: ${error}`);
            return;
        }
        console.log(`Python Executable Used by Electron: ${stdout}`);
    });
}

function setupOpenFileButton() {
    const openFileBtn = document.getElementById('openFileBtn');
    openFileBtn.onclick = async () => {
        openFileBtn.innerText = "Selecting file...";

        try {
            const result = await dialog.showOpenDialog({ properties: ['openFile'] });
            if (!result.canceled && result.filePaths.length > 0) {
                const filePath = result.filePaths[0];
                console.log(`Path of selected file: ${filePath}`);
                await runPythonScript(filePath);
            } else {
                openFileBtn.innerText = "Open File";
            }
        } catch (err) {
            console.error('Error selecting file:', err);
        }
    };
}

async function runPythonScript(filePath) {
    const openFileBtn = document.getElementById('openFileBtn');
    const notificationText = document.getElementById('notificationText');

    openFileBtn.innerText = "Loading...";
    const scriptPath = path.join(__dirname, 'main.py');
    const pythonProcess = spawn('python3', [scriptPath, filePath]);

    pythonProcess.stdout.on('data', async (data) => {
        console.log(`Python Output: ${data}`);
        const dataStr = data.toString().trim();

        if (dataStr !== "REQUEST_OUTPUT_PATH") {
            notificationText.innerText = data;
        } else {
            try {
                const saveResult = await dialog.showSaveDialog({
                    buttonLabel: 'Save file',
                    defaultPath: `vid-${Date.now()}.csv`
                });

                if (!saveResult.canceled && saveResult.filePath) {
                    const outputPath = saveResult.filePath;
                    console.log(`Path of selected output directory: ${outputPath}`);
                    pythonProcess.stdin.write(outputPath + '\n');
                } else {
                    notificationText.innerText = "No output file selected.";
                }
            } catch (err) {
                console.error('Error selecting output file:', err);
            }
            openFileBtn.innerText = "Open File";
            setupOpenFileButton();
        }
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`Python Error: ${data}`);
    });
}

// Start the application
initializeApp();
