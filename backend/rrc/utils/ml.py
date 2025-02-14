import torch


def get_default_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    else:
        raise RuntimeError("No cuda or mps device available")


DEFAULT_DEVICE = get_default_device()
