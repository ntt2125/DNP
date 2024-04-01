#! /bin/bash

TMUX_SES_NAME="ntt"
tmux new-session -d -s $TMUX_SES_NAME

tmux send-keys -t $TMUX_SES_NAME:0 'docker-compose up' C-m 

sleep 5

tmux new-window -t $TMUX_SES_NAME
tmux send-keys -t $TMUX_SES_NAME:1 'python create_topics.py' C-m
tmux send-keys -t $TMUX_SES_NAME:1 'python Save_video_process.py' C-m

tmux new-window -t $TMUX_SES_NAME
tmux send-keys -t $TMUX_SES_NAME:2 'python Pose_Process.py' C-m

tmux new-window -t $TMUX_SES_NAME
tmux send-keys -t $TMUX_SES_NAME:3 'python Tracking_process.py' C-m

sleep 5
tmux new-window -t $TMUX_SES_NAME
tmux send-keys -t $TMUX_SES_NAME:4 'python Read_frame_process.py' C-m