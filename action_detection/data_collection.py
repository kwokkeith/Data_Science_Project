import cv2
import numpy as np
import os
import mediapipe as mp
import argparse
from utils import draw_styled_landmarks, extract_keypoints, \
    mediapipe_detection, find_first_available_camera

mp_holistic = mp.solutions.holistic  # Holistic model
mp_drawing = mp.solutions.drawing_utils  # Drawing Utilities


def setup_folders(data_path, actions, no_sequences):
    """Cleans up empty folders and sets up directories for data collection."""
    os.makedirs(data_path, exist_ok=True)  # Ensure base directory exists

    for action in actions:
        action_path = os.path.join(data_path, action)
        os.makedirs(action_path, exist_ok=True)

        # Remove empty sequence folders
        existing_sequences = []
        for folder in os.listdir(action_path):
            folder_path = os.path.join(action_path, folder)
            if os.path.isdir(folder_path):
                if not os.listdir(folder_path):  # Folder is empty, remove it
                    os.rmdir(folder_path)
                else:
                    try:
                        existing_sequences.append(int(folder))
                    except ValueError:
                        pass  # Ignore non-numeric folder names

        # Start numbering from the next available sequence number
        start_sequence = max(existing_sequences, default=-1) + 1

        # Create new sequence folders
        for sequence in range(start_sequence, start_sequence + no_sequences):
            sequence_path = os.path.join(action_path, str(sequence))
            os.makedirs(sequence_path, exist_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--actions",
                        type=str, required=True, nargs='+',
                        help="actions to collect data for")
    parser.add_argument("--ns", type=int, default=30,
                        help="number of sequences to collect")
    parser.add_argument("--sl", type=int, default=60,
                        help="number of frames to collect per sequence")
    parser.add_argument("--mpdc", type=float, default=0.5,
                        help="Minimum detection confidence mediapipe model")
    parser.add_argument("--mptc", type=float, default=0.5,
                        help="Minimum tracking confidence mediapipe model")
    parser.add_argument("--wait", type=int, default=2000,
                        help="Wait time (ms) in between collection frames")
    args = parser.parse_args()
    print(f"actions to record {args.actions}")

    # path for exported data, numpy arrays
    data_path = os.path.join('mp_data')

    # actions to detect
    actions = np.array(args.actions)

    # number of videos worth of data
    no_sequences = args.ns

    # if videos are going to be 30 frames in length
    # 30 frames would be used to detect the action
    # 30 * 1662 keypoints data to detect the action
    sequence_length = args.sl

    # Activates video camera and captures sequences of actions
    # Find the first available camera
    camera_index = find_first_available_camera()

    if camera_index is None:
        print("Unable to find a camera that is available")
        return

    cap = cv2.VideoCapture(camera_index)

    # Only setup collection folder if we can open the videocapture
    # Setup collection folders
    setup_folders(data_path, actions, no_sequences)

    # Set mediapipe model
    with mp_holistic.Holistic(min_detection_confidence=args.mpdc,
                              min_tracking_confidence=args.mptc) as holistic:
        # Loop through actions
        for action in actions:
            # Loop through sequences aka videos
            for sequence in range(no_sequences):
                # Loop through video length aka sequence length
                for frame_num in range(sequence_length):

                    # Read feed
                    ret, frame = cap.read()

                    # Make detections to get landmarks face, shoulder and hands
                    image, results = mediapipe_detection(frame, holistic)

                    # Draw landmarks
                    draw_styled_landmarks(image, results)

                    # Apply wait logic
                    # (so that we can take a break before recollecting data)
                    # Display text to give instructions and state
                    if frame_num == 0:
                        cv2.putText(image, f"Collecting {action}...",
                                    (120, 200), cv2.FONT_HERSHEY_SIMPLEX,
                                    1, (0, 255, 0), 4, cv2.LINE_AA)
                        cv2.putText(image,
                                    f"Collecting frames for {action}" +
                                    f"Video Number {sequence}",
                                    (15, 12), cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5, (0, 0, 255), 1, cv2.LINE_AA)
                        # Show to screen
                        cv2.imshow('OpenCV Feed', image)
                        cv2.waitKey(args.wait)
                    else:
                        cv2.putText(image,
                                    f"Collecting frames for {action}" +
                                    f"Video Number {sequence}",
                                    (15, 12), cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5, (0, 0, 255), 1, cv2.LINE_AA)
                        # Show to screen
                        cv2.imshow('OpenCV Feed', image)

                    # Export keypoints
                    keypoints = extract_keypoints(results)
                    npy_path = os.path.join(
                        data_path, action, str(sequence), str(frame_num))
                    np.save(npy_path, keypoints)

                    # Break gracefully
                    if cv2.waitKey(10) & 0xFF == ord('q'):
                        break

        # Release captures
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
