import utils
from evaluate_model import evaluate_model
from tensorflow.keras.optimizers import AdamW, SGD, Adam
from tensorflow.keras.callbacks import TensorBoard, EarlyStopping
import os
import argparse
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, ConvLSTM2D, \
    MaxPooling3D, TimeDistributed, Dropout, Flatten, BatchNormalization, \
    SpatialDropout1D


def load_dataset(dataset_dir):
    """Loads the training and testing dataset from the specified directory."""
    X_train_path = os.path.join(dataset_dir, "X_train.npy")
    X_test_path = os.path.join(dataset_dir, "X_test.npy")
    Y_train_path = os.path.join(dataset_dir, "Y_train.npy")
    Y_test_path = os.path.join(dataset_dir, "Y_test.npy")

    if not all(os.path.exists(path)
               for path in
               [X_train_path, X_test_path, Y_train_path, Y_test_path]):
        print(f"Error: One or more files are missing in {dataset_dir}")
        exit(1)

    X_train = np.load(X_train_path)
    X_test = np.load(X_test_path)
    Y_train = np.load(Y_train_path)
    Y_test = np.load(Y_test_path)

    return X_train, X_test, Y_train, Y_test


def get_model_save_path(base_dir, dataset_name, optimizer, epochs):
    """Generates a unique folder name to save model weights"""
    model_dir = os.path.join(
        base_dir, f"{dataset_name}_{optimizer}_epochs{epochs}")

    # List existing models with the same prefix
    existing_models = [folder for folder in os.listdir(
        base_dir) if folder.startswith(
            f"{dataset_name}_{optimizer}_epochs{epochs}")]

    # Assign the next available version
    # If folders exist, create the next numbered version
    next_index = len(existing_models)
    save_path = os.path.join(model_dir + f"_{next_index}")

    # Create directory if not exists
    os.makedirs(save_path, exist_ok=True)
    return save_path


def main():
    parser = argparse.ArgumentParser(
        description="Train an LSTM model for action recognition")
    parser.add_argument("--dataset", type=str, required=True,
                        help="Path to the dataset folder " +
                        "(e.g., mp_data_processed/skip_2_testsize_10_0)")
    parser.add_argument("--epochs", type=int, default=500,
                        help="Number of epochs for training")
    parser.add_argument("--optimizer", type=str,
                        default="Adam",
                        choices=["Adam", "SGD", "AdamW"],
                        help="Optimizer to use for the model")
    parser.add_argument("--rate", type=float,
                        default=0.001,
                        help="Learning rate for the model")
    parser.add_argument('--early', default=False,
                        action=argparse.BooleanOptionalAction,
                        help="Whether to use early stop heuristic")

    args = parser.parse_args()

    dataset_path = args.dataset
    # Extract dataset folder name
    dataset_name = os.path.basename(dataset_path)

    # Load dataset
    X_train, X_test, Y_train, Y_test = load_dataset(dataset_path)

    # Extract actions count (number of classes)
    actions_count = Y_train.shape[1]  # Based on one-hot encoded labels

    # Setup TensorBoard
    log_dir = os.path.join("Logs")
    tb_callback = TensorBoard(log_dir=log_dir)

    # Setup early stopping callbacks
    early_stopping_callback = EarlyStopping(monitor='val_loss',
                                            patience=25,
                                            mode='min',
                                            restore_best_weights=True)

    # Build the LSTM Model
    model = Sequential()

    # Define model architecture
    ###################################################################
    # LSTM only
    """
    model.add(LSTM(64,
                   return_sequences=True,
                   recurrent_dropout=0.25,
                   dropout=0.3,
                   activation='relu',
                   input_shape=(X_train.shape[1], X_train.shape[2])))
    model.add(LSTM(128,
                   return_sequences=True,
                   recurrent_dropout=0.25,
                   dropout=0.3,
                   activation='relu'))
    model.add(LSTM(64,
                   return_sequences=False,
                   recurrent_dropout=0.25,
                   dropout=0.3,
                   activation='relu'))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(32, activation='relu'))
    # Output layer with softmax activation
    model.add(Dense(actions_count, activation='softmax'))
    ###################################################################
"""
    ###################################################################
    # LSTM only

    model.add(SpatialDropout1D(0.3))

    model.add(LSTM(64,
                   return_sequences=True,
                   recurrent_dropout=0.25,
                   dropout=0.3,
                   activation='relu',
                   input_shape=(X_train.shape[1], X_train.shape[2])))
    model.add(BatchNormalization())

    model.add(LSTM(128,
                   return_sequences=True,
                   recurrent_dropout=0.25,
                   dropout=0.3,
                   activation='relu'))
    model.add(BatchNormalization())

    model.add(LSTM(64,
                   return_sequences=False,
                   recurrent_dropout=0.25,
                   dropout=0.3,
                   activation='relu'))
    model.add(BatchNormalization())

    model.add(Dense(64, activation='relu'))
    model.add(Dense(32, activation='relu'))
    # Output layer with softmax activation
    model.add(Dense(actions_count, activation='softmax'))
    ###################################################################
    """
    ###################################################################
    # ConvLSTM
    SEQUENCE_LENGTH = 30
    IMAGE_HEIGHT = 30
    IMAGE_WIDTH = 30
    model.add(ConvLSTM2D(filters=4, kernel_size=(3, 3), activation='tanh',
                         data_format="channels_last",
                         recurrent_dropout=0.2,
                         return_sequences=True,
                         input_shape=(SEQUENCE_LENGTH,
                                      IMAGE_HEIGHT,
                                      IMAGE_WIDTH,
                                      3)))
    model.add(MaxPooling3D(pool_size=(1, 2, 2),
                           padding='same',
                           data_format='channels_last'))
    model.add(TimeDistributed(Dropout(0.2)))

    model.add(ConvLSTM2D(filters=8,
                         kernel_size=(3, 3),
                         activation='tanh',
                         data_format="channels_last",
                         recurrent_dropout=0.2,
                         return_sequences=True))

    model.add(MaxPooling3D(pool_size=(1, 2, 2),
                           padding='same',
                           data_format="channels_last"))
    model.add(TimeDistributed(Dropout(0.2)))

    model.add(ConvLSTM2D(filters=14,
                         kernel_size=(3, 3),
                         activation='tanh',
                         data_format='channels_last',
                         recurrent_dropout=0.2,
                         return_sequences=True))

    model.add(MaxPooling3D(pool_size=(1, 2, 2),
                           padding='same',
                           data_format='channels_last'))
    model.add(TimeDistributed(Dropout(0.2)))

    model.add(ConvLSTM2D(filters=16,
                         kernel_size=(2, 2),
                         activation='tanh',
                         data_format='channels_last',
                         recurrent_dropout=0.2,
                         return_sequences=True))

    model.add(MaxPooling3D(pool_size=(1, 2, 2),
                           padding='same',
                           data_format='channels_last'))

    model.add(Flatten())
    model.add(Dense(actions_count, activation='softmax'))
    ###################################################################
    """

    # Compile Model
    if args.optimizer == "Adam":  # For most cases
        model.compile(optimizer=Adam(learning_rate=args.rate),
                      loss='categorical_crossentropy',
                      metrics=['categorical_accuracy'])
    elif args.optimizer == "SGD":  # Best for generalisation
        model.compile(optimizer=SGD(learning_rate=args.rate,
                                    momentum=0.9),
                      loss='categorical_crossentropy',
                      metrics=['categorical_accuracy'])
    elif args.optimizer == "AdamW":  # Better Regularisation
        model.compile(optimizer=AdamW(learning_rate=args.rate,
                                      weight_decay=1e-4),
                      loss='categorical_crossentropy',
                      metrics=['categorical_accuracy'])
    else:
        print("Failed model compilation, model not compatible")

    print("Training model...")
    print("Use tensorboard --logdir=/Logs/train to access tensorboard gui")

    # Train Model
    try:
        if args.early:
            model_training_history = model.fit(X_train, Y_train,
                                               epochs=args.epochs,
                                               shuffle=True,
                                               validation_split=0.2,
                                               callbacks=[tb_callback,
                                                          early_stopping_callback])
        else:
            model_training_history = model.fit(X_train, Y_train,
                                               epochs=args.epochs,
                                               shuffle=True,
                                               validation_split=0.2,
                                               callbacks=[tb_callback])
    except KeyboardInterrupt:
        pass
    finally:
        # Print Model Summary
        print(model.summary())

        # Get save path for model weights
        os.makedirs("Saved_Models", exist_ok=True)
        model_save_path = get_model_save_path(
            "Saved_Models", dataset_name, args.optimizer, args.epochs)

        # Get plot of model_training_history
        # Visualise training and validation loss metrics
        plot_1 = utils.plot_metric(model_training_history,
                                   'loss',
                                   'val_loss',
                                   'Total Loss vs Total validation Loss')
        plot_1.savefig(os.path.join(model_save_path, "Loss"))
        plot_1.close()
        # visualise training and validation accuracy metrics
        plot_2 = utils.plot_metric(model_training_history,
                                   'categorical_accuracy',
                                   'val_categorical_accuracy',
                                   'Total Accuracy vs Total Validation Accuracy')
        plot_2.savefig(os.path.join(model_save_path, "Accuracy"))
        plot_2.close()

        # Save Model Weights
        weights_file = os.path.join(
            model_save_path, "model_weights.weights.h5")
        model.save_weights(weights_file)
        model.save(os.path.join(model_save_path, 'model.h5'))

        print(f"Model weights saved at: {weights_file}")

        evaluate_model(model, X_test, Y_test)


if __name__ == "__main__":
    main()
