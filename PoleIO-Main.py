import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QTextEdit, QWidget, QMessageBox, QInputDialog, QLCDNumber, QPlainTextEdit
from PyQt5.QtGui import QColor, QTextCursor, QTextCharFormat
from PyQt5.QtCore import Qt, QThread
from PyQt5 import uic
from GetEXIFTags import extract_dji_metadata  # DJI XMP Metadata extractor
from GetEXIFTags import extract_value_from_xmp
from PieProgressBar import ProgressPie  # Import the custom widget
from ImgProcWorker import ImageProcessingWorker
import datetime
import shutil # Import for moving files
from concurrent.futures import ThreadPoolExecutor

####################################################################
class PoleIOApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # Check if running as a standalone PyInstaller executable
        if hasattr(sys, '_MEIPASS'):
            ui_path = os.path.join(sys._MEIPASS, 'PoleIO-UI.ui')
        else:
            ui_path = os.path.join(os.path.dirname(__file__), 'PoleIO-UI.ui')

        uic.loadUi(ui_path, self)
        
        # Hook up the buttons to their actions
        self.browseButton.clicked.connect(self.browse_folder)
        self.verifyButton.clicked.connect(self.verify_images)
        
        # Initialize logTextBox (make sure this is the correct name of your log text field)
        self.logOutput = self.findChild(QPlainTextEdit, "logTextView")  

        if self.logOutput is None:
            QMessageBox.critical(self, "Error", "logTextView not found in the UI. Please check the UI object name.")
            return
        
       # Initialize pie progress bar
        self.progressPieContainer = self.findChild(QWidget, "progressPieContainer")
        self.pieProgressBar = ProgressPie(self.progressPieContainer)  # Use ProgressPie instead of PieProgressBar
        self.pieProgressBar.setGeometry(self.progressPieContainer.rect())  # Match size

        # Initialize pole count LCD (updated object name)
        self.poleCountDisplay = self.findChild(QLCDNumber, "lcdPoleCount")  # Updated to "lcdPoleCount"
        
        # Placeholder for image folder path
        self.image_folder_path = None
        self.poleCountDisplay.display(0)  # Set initial value to 0

####################################################################
    
    def update_pie_progress(self, progress):
        # Update the pie progress bar based on the progress emitted by the worker
        self.pieProgressBar.setValue(progress)
    
    def processing_finished(self):
        # This method can handle when the image processing finishes
        self.log_message(f"Processing Completed!")
        self.verifyButton.setEnabled(True)


####################################################################


    def log_message(self, message, color=None):
        # Logs a message to the log text view with optional color.
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create a QTextCursor to interact with the logOutput text editor
        cursor = self.logOutput.textCursor()
        cursor.movePosition(QTextCursor.End)

        # Set the text color if specified
        if color:
            text_format = QTextCharFormat()
            text_format.setForeground(QColor(color))  # Set the desired color
            cursor.setCharFormat(text_format)

        # Insert the log message with the specified color
        cursor.insertText(f"{current_time}: {message}\n")

        # Move the cursor to the end to ensure new messages are appended properly
        self.logOutput.moveCursor(QTextCursor.End)

####################################################################
    
    def browse_folder(self):
        try:
            # Open a file dialog to select the image folder
            folder = QFileDialog.getExistingDirectory(self, "Select Folder")
            if folder:
                self.imageFolderInput.setText(folder)  # Display the selected folder path
                self.image_folder_path = folder
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while selecting a folder: {e}")
            self.log_message(f"Error while selecting folder: {e}")



####################################################################

    def verify_images(self):
        if not self.image_folder_path:
            self.log_message("Please provide a valid folder path.")
            return
    
        try:
            # Prevent starting a new thread if the previous one is still running
            if hasattr(self, 'thread') and isinstance(self.thread, QThread) and self.thread.isRunning():
                self.log_message("Processing is already running. Please wait.")
                return
            
            # Get the full path of the image folder
            full_folder_path = os.path.abspath(self.image_folder_path)
            self.log_message(f"Processing images from folder: {full_folder_path}")

            #Disable the button
            self.verifyButton.setEnabled(False)
        

            # Check if the "Node Name" text box has a value first
            node_name = self.textNodeName.toPlainText().strip()
            if node_name:
                output_folder_name = node_name  # Use the value from the text box
            else:
                # If no value, ask the user to provide the name for the output folder
                output_folder_name, ok = QInputDialog.getText(self, "Enter Output Folder Name", "Output Folder Name:")
                if not ok or not output_folder_name:
                    self.log_message("No output folder name provided. Aborting.")
                    return
                
                if not ok or not output_folder_name:
                    self.log_message("No output folder name provided. Aborting.")
                    return

            # Create the output folder inside the full folder path (not in the parent directory)
            output_folder_path = os.path.join(full_folder_path, output_folder_name)
            # Print the output folder path
            #print(f"Joined output folder path: {output_folder_path}")


            if not os.path.exists(output_folder_path):
                os.makedirs(output_folder_path)
                self.log_message(f"Created output folder at: {output_folder_path}")

            # Recursively collect all image files from the folder and subfolders
            image_files = self.collect_images(full_folder_path)
            
            self.log_message(f"Found {len(image_files)} images...") 

            # Create a QThread and move the worker to that thread
            self.thread = QThread()
            self.worker = ImageProcessingWorker(image_files, output_folder_path)
            self.worker.moveToThread(self.thread)

            # Connect worker signals
            self.worker.progress.connect(self.update_pie_progress)  # Connect progress to update method
            self.worker.log_message_signal.connect(self.log_message)  # Connect log signal
            self.worker.finished.connect(self.processing_finished)   # Connect finished signal
            self.worker.pole_count_signal.connect(self.poleCountDisplay.display) # Connect the pole count LCD
            self.worker.finished.connect(self.thread.quit)  # Quit the thread when finished
            self.worker.finished.connect(self.worker.deleteLater)  # Clean up the worker
            self.thread.finished.connect(self.thread.deleteLater)  # Clean up the thread

            # Start processing when the thread starts
            self.thread.started.connect(self.worker.process_image_sequence)

            # Start the thread
            self.thread.start()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Verify Images: Exception Thrown: {e}")
            self.log_message(f"Exception thrown in Verify Images: {e}")

############################################################################################
    def collect_images(self, folder_path):
        """ Recursively collect all image files from the folder and subfolders, sorted by name. """
        image_files = []
        for root, dirs, files in os.walk(folder_path):  # Recursively walk through all subdirectories
            for file in sorted(files):  # Sort files by name (which includes timestamp)
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):  # Only image files
                    image_files.append(os.path.join(root, file))
        return image_files

############################################################################################
    

   
            

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PoleIOApp()
    window.show()
    sys.exit(app.exec_())