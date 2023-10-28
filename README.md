This desktop app is intended to scan a given video or instagram reel for text which appears on-screen, and scrape it into a .csv

Current Tech Stack:

Frontend: Electron Forge

Backend: OpenCV, Pytesseract, numpy

Important: In order to be distributable as an .exe without requiring the user to install additional files separately, the project has embedded Python and Tesseract, which has been excluded from the git repository.
If you wish to run the project from the source files, you need to add these excluded files.
You can do that by doing the following:

1. In your terminal in the project's root folder, run the command: ```python -m venv myappenv```
2. Activate the virtual environment, and run the following command:
    - On Windows: ```myappenv\Scripts\activate```
    - On macOS/Linux: ```source myappenv/bin/activate```
3. Install [Tesseract-OCR](https://github.com/tesseract-ocr/tesseract#installing-tesseract) and place the Tesseract-OCR folder inside the root folder (should be in the same directory as myappenv)
3. Install the necessary python libraries: [OpenCV](https://pypi.org/project/opencv-python/), [PyTesseract](https://pypi.org/project/pytesseract/) and [TheFuzz](https://pypi.org/project/thefuzz/) as per their installation instructions
4. Run the commands:
```npm install
npm start```

To package the app, run ```npx electron-packager .```