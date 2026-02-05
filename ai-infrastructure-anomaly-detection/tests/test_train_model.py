import pandas as pd

from train_model import split_data


def test_split_data_shapes():
    df = pd.DataFrame(
        {
            "cpu_usage": list(range(100)),
            "memory_usage": list(range(100, 200)),
            "network_load": list(range(200, 300)),
        }
    )

    X_train, X_val, X_test = split_data(df, test_size=0.15, val_size=0.15, random_state=42)
    assert X_train.shape[1] == 3
    assert X_val.shape[1] == 3
    assert X_test.shape[1] == 3
    assert len(X_train) + len(X_val) + len(X_test) == len(df)