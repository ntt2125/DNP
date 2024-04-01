#! /bin/bash

# Change the directory to your project here
DIRS="/home/ntthong/NTT/Lab_iai/DNP"

# Change the conda env
ENVS="dnp"

#this is use for vs code only
unset GTK_PATH

source activate $ENVS

#python "$DIRS/create_topics.py"

# If you dont want the terminal showed up, delete all "gnome-terminal -- "

gnome-terminal -- python "$DIRS/Save_video_process.py" &

gnome-terminal -- python "$DIRS/Pose_Process.py" &

gnome-terminal -- python "$DIRS/Tracking_process.py" &

sleep 6

gnome-terminal -- python "$DIRS/Read_frame_process.py" &

