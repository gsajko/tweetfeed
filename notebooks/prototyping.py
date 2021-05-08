from argparse import Namespace
from argparse import Namespace
from pathlib import Path

import mlflow

# %%
params = Namespace(
    char_level=True,
    filter_sizes=list(range(1, 11)),
    batch_size=64,
    embedding_dim=128,
    num_filters=128,
    hidden_dim=128,
    dropout_p=0.5,
    lr=2e-4,
    num_epochs=200,
    patience=10,
)

# %%
EXPERIMENTS_DIR = Path("experiments")
Path(EXPERIMENTS_DIR).mkdir(exist_ok=True)  # create experiments dir
mlflow.set_tracking_uri("file://" + str(EXPERIMENTS_DIR.absolute()))
# %%
