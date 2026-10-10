# FRAMEWORK - DO NOT EDIT (identical across all teams; the organizers use their own copy)
import os, pickle

STATE_FILE = "model_state.pkl"


def save_model(model, state_dir):
    os.makedirs(state_dir, exist_ok=True)
    with open(os.path.join(state_dir, STATE_FILE), "wb") as f:
        pickle.dump(model, f)


def load_model(state_dir):
    with open(os.path.join(state_dir, STATE_FILE), "rb") as f:
        return pickle.load(f)
