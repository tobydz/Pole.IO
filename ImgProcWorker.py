from PyQt5.QtCore import QObject, pyqtSignal, QThread
from PyQt5.QtWidgets import QMessageBox
from GetEXIFTags import extract_dji_metadata, extract_value_from_xmp
import shutil
import os

class ImageProcessingWorker(QObject):
    progress = pyqtSignal(int)  # Signal to send progress updates to the UI
    finished = pyqtSignal()     # Signal to notify when processing is done
    log_message_signal = pyqtSignal(str, str)  # Signal to send log messages
    pole_count_signal = pyqtSignal(int) # Pole Count


    def __init__(self, image_files, output_folder):
        super().__init__()
        self.image_files = image_files
        self.output_folder = output_folder
#####################################################################
    def process_image_sequence(self):
        nadir_found = False
        zoom_found = False
        orbit_count = 0
        pole_count = 0
        incomplete_sequence = False
        valid_sequence = []

        # Initialize counters for tracking the total images, sequences, and issues
        total_images_processed = 0  # Initialize it to 0
        total_valid_sequences = 0
        total_poles = 0
        total_broken_sequences = 0
        duplicate_nadir_count = 0
        duplicate_zoom_count = 0
        missing_nadir_count = 0
        missing_zoom_count = 0

        total_images = len(self.image_files)

        for idx, image_file in enumerate(self.image_files):
            image_path = image_file
            total_images_processed += 1
            
            # Use the updated DJI EXIF extraction method
            xmp_block = extract_dji_metadata(image_path)
            if xmp_block is None:
                self.log_message_signal.emit(f"Failed to extract metadata for {image_file}", "red")
                continue

            # Log extracted XMP block for debugging
            # self.log_message_signal.emit(f"Extracted XMP block from {image_file}: {xmp_block.get('XMP', '')[:200]}...")   # Log first 200 chars of the XMP field  # Log first 200 chars

            # Search for GimbalPitchDegree and ImageSource in XMP block
            gimbal_pitch = extract_value_from_xmp(xmp_block, "drone-dji:GimbalPitchDegree", self.log_message_signal.emit)
            image_source = extract_value_from_xmp(xmp_block, "drone-dji:ImageSource", self.log_message_signal.emit) 

            # Log extracted metadata for debugging
            #self.log_message_signal.emit(f"Gimbal Pitch: {gimbal_pitch}, Image Source: {image_source} from {image_file}")

            # Check for NADIR (start of a sequence)
            if gimbal_pitch is not None and float(gimbal_pitch) <= -89:
                self.log_message_signal.emit(f"NADIR shot detected: {image_file} with pitch {gimbal_pitch}","orange")
                if nadir_found:
                    duplicate_nadir_count += 1  # Count as duplicate NADIR shot
                    continue  # Skipping debug message for multiple NADIR shots
                else:
                    nadir_found = True
                    incomplete_sequence = True  # A sequence has started
                    valid_sequence.append({"path": image_path, "type": "nadir"})

            # Check for zoom shots using ImageSource
            if image_source == "ZoomCamera":
                self.log_message_signal.emit(f"Zoom shot detected: {image_file}","magenta")
                if zoom_found:
                    duplicate_zoom_count += 1 # Count duplicate zoom shots
                    continue  # Skipping debug message for multiple zoom shots
                else:
                    zoom_found = True
                    valid_sequence.append({"path": image_path, "type": "zoom"})

                    # A valid sequence is found when NADIR and orbit shots precede a zoom shot
                    if nadir_found and orbit_count >= 25:
                        pole_count += 1
                        total_valid_sequences += 1  # Increment valid sequences count
                        total_poles += 1  # Count unique poles based on zoom shots

                        self.move_images_batch(valid_sequence, self.output_folder)
                        self.log_message_signal.emit(f"Valid pole sequence #{pole_count} completed.", "green")
                        # Update the LCD display with the current pole count
                        self.pole_count_signal.emit(pole_count)
                    else:
                        # Sequence is incomplete, increment broken sequences only if NADIR or Zoom is missing
                        self.log_message_signal.emit("Incomplete sequence, missing orbit shots, NADIR, or Zoom.", "red")
                        if not nadir_found or not zoom_found:  # Check if either NADIR or Zoom is missing
                            total_broken_sequences += 1
                            if not nadir_found:
                                missing_nadir_count += 1  # Increment missing NADIR counter
                            if not zoom_found:
                                missing_zoom_count += 1  # Increment missing ZOOM counter
                    valid_sequence.clear()

                    # Reset sequence tracking
                    nadir_found = False
                    zoom_found = False
                    orbit_count = 0
                    incomplete_sequence = False  # Reset after valid sequence

            # Count orbit shots (assuming orbit is anything between NADIR and zoom)
            if gimbal_pitch is not None and float(gimbal_pitch) > -89 and image_source == "WideCamera":
                orbit_count += 1
                valid_sequence.append({"path": image_path, "type": "orbit"})
                self.log_message_signal.emit(f"Orbit shot detected: {image_file}","blue")

            
            # Calculate the progress as a percentage and update the progress bar
            progress = (idx + 1) / total_images * 100
            self.progress.emit(progress)

        # Final validation after processing
        if incomplete_sequence:
            first_image = valid_sequence[0]['path'] if valid_sequence else "Unknown"
            last_image = valid_sequence[-1]['path'] if valid_sequence else "Unknown"
            self.log_message_signal.emit(f"Incomplete sequence found between {first_image} and {last_image}.", "red")

        # Log the final tally with newlines for readability
        self.log_message_signal.emit(f"Total Images Processed: {total_images_processed}\n", "black")
        self.log_message_signal.emit(f"Total Valid Pole Sequences: {total_valid_sequences}\n", "black")
        self.log_message_signal.emit(f"Total Poles (unique zoom shots): {total_poles}\n", "black")
        self.log_message_signal.emit(f"Total Broken Image Sequences: {total_broken_sequences}\n", "black")
        self.log_message_signal.emit(f"Duplicate NADIR Shots: {duplicate_nadir_count}\n", "black")
        self.log_message_signal.emit(f"Duplicate Zoom Shots: {duplicate_zoom_count}\n", "black")
        self.log_message_signal.emit(f"Broken Sequences due to missing NADIR: {missing_nadir_count}\n", "black")
        self.log_message_signal.emit(f"Broken Sequences due to missing ZOOM: {missing_zoom_count}\n", "black")
        
        self.log_message_signal.emit(f"Total valid pole sequences: {pole_count}", "black")

#####################################################################

 # New method to move a batch of images (the valid sequence)
    def move_images_batch(self, image_paths, output_folder):
        try:
            # Extract only the 'path' from each dictionary in image_paths
            for img in image_paths:
                image_path = img['path']  # Get the file path from the dictionary
                shutil.move(image_path, os.path.join(output_folder, os.path.basename(image_path)))
            self.log_message_signal.emit(f"Moved {len(image_paths)} images to {output_folder}", "black")
        except Exception as e:
            self.log_message_signal.emit(f"Error moving images: {e}", "black")
            QMessageBox.critical(self, "Error", f"An error occurred while moving images: {e}", "black")