from types import CellType

from mlflow.tracking import MlflowClient

# %%


client = MlflowClient()
experiments = (
    client.list_experiments()
)  # returns a list of mlflow.entities.Experiment


# %%
