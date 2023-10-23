const { remote } = require('electron');
const { dialog } = remote;
const { spawn } = require('child_process'); // Import the spawn function
const path = require('path');

const { exec } = require('child_process');
exec('python -u -c "import sys; print(sys.executable)"', (error, stdout, stderr) => {
    if (error) {
        console.error(`Python Error: ${error}`);
        return;
    }
    console.log(`Python Executable Used by Electron: ${stdout}`);
});

const openFileBtn = document.getElementById('openFileBtn');
const notificationText = document.getElementById('notificationText');
openFileBtn.onclick = e => {
  openFileBtn.innerText = "Selecting file...";
  dialog.showOpenDialog({
    properties: ['openFile']
  }).then(result => {
    if (!result.canceled && result.filePaths.length > 0) {
      openFileBtn.innerText = "Loading...";
      const filePath = result.filePaths[0];
      console.log(`Path of selected file: ${filePath}`);
      
      // Run the Python script with the selected file as an argument
      
      const scriptPath = path.join(__dirname, 'main.py');
      const pythonProcess = spawn('python3', [scriptPath, filePath]);

      pythonProcess.stdout.on('data', (data) => {
        console.log(`Python Output: ${data}`);
        if(data.toString().trim() != "REQUEST_OUTPUT_PATH") {
          notificationText.innerText = data;
        } else {
          notificationText.innerText = "Selecting output file...";
          dialog.showSaveDialog({
            buttonLabel: 'Save file',
            defaultPath: `vid-${Date.now()}.csv`
          }).then(result => {
            if (!result.canceled && result.filePath) {
                const outputPath = result.filePath;
                console.log(`Path of selected output directory: ${outputPath}`);
                pythonProcess.stdin.write(outputPath + '\n');
            } else {
                notificationText.innerText = "No output file selected.";
            }
          }).catch(err => {
              console.error('Error selecting output file:', err);
          });
        
        }
      });

      pythonProcess.stderr.on('data', (data) => {
        console.error(`Python Error: ${data}`);
      });

    } else {
      openFileBtn.innerText = "Open File";
    }
  }).catch(err => {
    console.error('Error selecting file:', err);
  });
};
