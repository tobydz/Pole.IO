import os
import re
from PIL import Image

def extract_value_from_xmp(xmp_block, tag_name, log_message_func):
    """Helper function to extract a specific tag's value from the XMP block"""
    try:
        if not xmp_block or not isinstance(xmp_block, dict) or 'XMP' not in xmp_block:
            log_message_func(f"Invalid or unrelated XMP block for {tag_name}: {type(xmp_block)}")
            return None

        # Extract and process the XMP data
        xmp_data = xmp_block['XMP']
        start_index = xmp_data.find(tag_name)
        if start_index == -1:
            return None
        end_index = xmp_data.find('"', start_index + len(tag_name) + 2)
        return xmp_data[start_index + len(tag_name) + 2:end_index]
        
    except Exception as e:
        log_message_func(f"Error extracting {tag_name} from XMP block: {str(e)}")
        return None

# Function to extract DJI-specific metadata (focus on MakerNote and XMP)
def extract_dji_metadata(image_path):
    metadata = {}
    
    try:
        # Open the image file
        image = Image.open(image_path)
        # Get EXIF data
        exif_data = image._getexif()

        if exif_data is not None:
            # Extract MakerNote field (usually contains proprietary DJI data)
            maker_note = exif_data.get(37500)  # 37500 is the standard tag ID for MakerNote
            
            if maker_note:
                metadata['MakerNote'] = maker_note
            else:
                metadata['MakerNote'] = None

            # Attempt to find and extract XMP data manually
            xmp_data = extract_xmp_block(image_path)
            if xmp_data:
                metadata['XMP'] = xmp_data

        else:
            metadata['EXIF'] = None
    
    except Exception as e:
        print(f"Error extracting DJI metadata: {e}")
        metadata['Error'] = str(e)
    
    return metadata

# Function to extract XMP block from image
def extract_xmp_block(image_path):
    try:
        # Read the image file as binary
        with open(image_path, 'rb') as f:
            img_data = f.read()

        # Find the XMP block (likely contains DJI-specific metadata)
        xmp_start = img_data.find(b'<x:xmpmeta')
        xmp_end = img_data.find(b'</x:xmpmeta>') + 12  # Include closing tag length

        if xmp_start != -1 and xmp_end != -1:
            # Extract the entire XMP block
            xmp_block = img_data[xmp_start:xmp_end].decode('utf-8', errors='ignore')
            return xmp_block
        else:
            return None

    except Exception as e:
        print(f"Error extracting XMP data: {e}")
        return None
    

####################################################################

    def extract_value_from_xmp(self, xmp_block, tag_name):

        #"""Helper function to extract a specific tag's value from the XMP block"""
        try:
            # Ensure xmp_block is valid and not None
            if not xmp_block or not isinstance(xmp_block, dict) or 'XMP' not in xmp_block:
                print(f"Invalid XMP block or data type provided for {tag_name}: {type(xmp_block)}")
                return None

            #print(f"Extracting {tag_name} from XMP block")

            tag_start = xmp_block.find(tag_name)
            if tag_start != -1:
                tag_start += len(tag_name) + 2  # Move past the tag name and '='
                tag_end = xmp_block.find('"', tag_start)

                # Ensure tag_end is valid before slicing
                if tag_end != -1:
                    return xmp_block[tag_start:tag_end]
                else:
                    print(f"Tag '{tag_name}' not properly closed in XMP block.")
            else:
                print(f"Tag '{tag_name}' not found in XMP block.")
        except Exception as e:
            print(f"Error extracting {tag_name} from XMP: {e}")
        return None
    
   

# Test with your DJI image (you can comment this out for the main program)
# image_path = 'DJI_NADIR.JPG'  # Update with your actual image path
# metadata = extract_dji_metadata(image_path)
# print(metadata)