# %%

import mlflow
# %%
exp_name: str = "default"
client = mlflow.tracking.MlflowClient()
print("searching for best model")
if exp_name == "default":
    experiment_id = len(client.list_experiments())
else:
    experiment_id = mlflow.get_experiment_by_name(exp_name).experiment_id

all_runs = client.search_runs(
    experiment_id, order_by=["metrics.f1_class1 DESC"]
)
best_run = all_runs[0].info.run_id
# %%
