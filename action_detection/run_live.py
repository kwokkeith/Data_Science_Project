import os
import cv2
import numpy as np
import argparse
from utils import mediapipe_detection, draw_styled_landmarks, \
    extract_keypoints, build_model, extract_optimizer_from_path, \
    find_first_available_camera
import mediapipe as mp
from tensorflow.keras.models import load_model
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense

# Initialize Mediapipe
mp_holistic = mp.solutions.holistic


def get_model_input_shape(weights_path):
    """Loads the model architecture and extracts its input shape."""

    # Define your model architecture (must match the original training structure)
    model = Sequential([
        LSTM(64, return_sequences=True, activation='relu',
             input_shape=(30, 1662)),  # Use default shape
        LSTM(128, return_sequences=True, activation='relu'),
        LSTM(64, return_sequences=False, activation='relu'),
        Dense(64, activation='relu'),
        Dense(32, activation='relu'),
        # Adjust number of actions (classes) accordingly
        Dense(5, activation='softmax')
    ])

    # Load the weights
    model.load_weights(weights_path)

    # Extract input shape
    # (sequence_length, feature_length)
    return model.input_shape[1], model.input_shape[2]


def main():
    parser = argparse.ArgumentParser(
        description="Run LSTM action recognition on live video feed")
    parser.add_argument("--weights", type=str, required=True,
                        help="Path to the trained model weights (.h5 file)")
    parser.add_argument("--dataset", type=str, required=True,
                        help="Path to the dataset folder containing data")
    parser.add_argument("--threshold", type=float, default=0.5,
                        help="Confidence threshold for predictions")
    parser.add_argument("--rate", type=float, default=0.001,
                        help="Learning rate of the model loaded")
    parser.add_argument("--mpdc", type=float, default=0.5,
                        help="Minimum detection confidence mediapipe model")
    parser.add_argument("--mptc", type=float, default=0.5,
                        help="Minimum tracking confidence mediapipe model")
    parser.add_argument("--freeze", type=int, default=10,
                        help="Number of predictions before a prediction \
                        is valid and displayed")
    parser.add_argument("--sentences", type=int, default=5,
                        help="Number of actions to keep and display")

    args = parser.parse_args()

    # Load dataset to retrieve actions
    actions = np.array([folder for folder in os.listdir(
        args.dataset) if os.path.isdir(os.path.join(args.dataset, folder))])
    num_classes = len(actions)

    # Extract sequence length from model
    sequence_length, feature_length = get_model_input_shape(args.weights)
    print(
        f"Model trained with sequence length: {sequence_length}, " +
        f"feature length: {feature_length}")

    # Load optimizer
    optimizer = extract_optimizer_from_path(args.weights, args.rate)

    # Build and compile the model with correct input shape
    model = build_model(input_shape=(
        sequence_length, feature_length), num_classes=num_classes)
    model.compile(optimizer=optimizer, loss='categorical_crossentropy',
                  metrics=['categorical_accuracy'])

    # Load trained weights
    model.load_weights(args.weights)
    print(f"Loaded model weights from: {args.weights}")

    # Initialize variables
    sequence = []
    sentence = []
    predictions = []
    threshold = args.threshold  # Confidence threshold

    # Find the first available camera
    camera_index = find_first_available_camera()

    if camera_index is None:
        print("Unable to find a camera that is available")
        return

    # Open webcam
    cap = cv2.VideoCapture(camera_index)

    # Set up Mediapipe model with user-defined confidence values
    with mp_holistic.Holistic(min_detection_confidence=args.mpdc,
                              min_tracking_confidence=args.mptc) as holistic:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Camera feed not available.")
                break

            # Make detections
            image, results = mediapipe_detection(frame, holistic)
            draw_styled_landmarks(image, results)

            # Extract keypoints
            keypoints = extract_keypoints(results)
            sequence.append(keypoints)
            # Adjust based on model input shape
            sequence = sequence[-sequence_length:]

            # Define text positions
            start_x, start_y = 30, 50
            line_spacing = 50  # Space between lines

            # Only run prediction when we have enough frames
            if len(sequence) == sequence_length:
                res = model.predict(np.expand_dims(sequence, axis=0))[
                    0]  # Get probabilities
                predicted_action = actions[np.argmax(res)]
                confidence = res[np.argmax(res)]

                predictions.append(np.argmax(res))

                # Check if action is stable across last 10 frames
                if len(predictions) > args.freeze and \
                        np.unique(
                            predictions[-args.freeze:])[0] == np.argmax(res):
                    if confidence > threshold:
                        if len(sentence) == 0 or \
                                predicted_action != sentence[-1]:
                            sentence.append(predicted_action)

                if len(sentence) > args.sentences:
                    # Keep last args.sentences actions
                    sentence = sentence[-args.sentences:]

                # Display action, confidence & accuracy
                cv2.putText(image, f"Action: {predicted_action}",
                            (start_x, start_y),
                            cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (255, 255, 255), 2, cv2.LINE_AA)
                cv2.putText(image, f"Confidence: {confidence:.2f}",
                            (start_x, start_y + line_spacing),
                            cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (255, 255, 255), 2, cv2.LINE_AA)

            # Move background rectangle JUST BELOW the confidence text
            # Start right after confidence text
            rect_y_start = start_y + 2 * line_spacing
            rect_y_end = rect_y_start + 40  # Make sure it’s not too tall

            cv2.rectangle(image, (0, rect_y_start),
                          (640, rect_y_end), (245, 117, 16), -1)

            # Display detected actions
            cv2.putText(image, ' '.join(sentence), (10, rect_y_start + 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1,
                        (255, 255, 255), 2, cv2.LINE_AA)

            # Show video feed
            cv2.imshow('Action Recognition', image)

            # Quit with 'q'
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
