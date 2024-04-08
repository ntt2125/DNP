import cv2

def count_frames(video_path):
    # Open the video file
    cap = cv2.VideoCapture(video_path)

    # Check if the video opened successfully
    if not cap.isOpened():
        print("Error: Could not open video.")
        return -1

    # Get the total number of frames
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Release the video capture object
    cap.release()

    return total_frames

def get_hight_width(video_file):

    # video_file = 'your_video_file.mp4'
    cap = cv2.VideoCapture(video_file)

    # Get width and height
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print("Width:", width)
    print("Height:", height)

    cap.release()


if __name__=='__main__':
    
# Path to your video file
    video_path = 'demo_input/video/demo_iai_1.mp4'

    # Call the function to count frames
    # num_frames = count_frames(video_path)
    
    get_hight_width(video_file=video_path)

    # if num_frames != -1:
        # print("Total frames in the video:", num_frames)
