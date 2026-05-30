import sys
import json
import argparse
import os
import contextlib

def main():
    parser = argparse.ArgumentParser(description="Logi-Hex TimesFM Forecasting Sidecar")
    parser.add_argument("--history", type=str, required=True, help="JSON string of historical data points (list of floats)")
    parser.add_argument("--horizon", type=int, default=30, help="Number of future points to predict")
    
    args = parser.parse_args()
    
    try:
        # 1. Parse historical data
        history_data = json.loads(args.history)
        if not isinstance(history_data, list):
            raise ValueError("History must be a JSON list of numbers")
            
        history = [float(x) for x in history_data]
        
        # TimesFM requires some historical data.
        # If history is empty or extremely short, pad/create a default history.
        if not history:
            history = [0.0]
            
        # 2. Invoke TimesFM with stdout silenced
        # We redirect stdout to devnull so that library print statements don't pollute the JSON output.
        with open(os.devnull, 'w') as devnull:
            with contextlib.redirect_stdout(devnull):
                import timesfm
                
                # We specify backend="cpu" for local CPU inference.
                # Under Windows, TimesFM uses PyTorch on CPU.
                tfm = timesfm.TimesFm(
                    hparams=timesfm.TimesFmHparams(
                        backend="cpu",
                        per_core_batch_size=32,
                        horizon_len=args.horizon,
                    ),
                    checkpoint=timesfm.TimesFmCheckpoint(
                        huggingface_repo_id="google/timesfm-1.0-200m-pytorch"
                    ),
                )
                
                forecast_input = [history]
                freq = [0]  # 0 = irregular/daily
                point_forecast, _ = tfm.forecast(forecast_input, freq=freq)
                
                # point_forecast shape is [batch_size, horizon_len]
                # We take the first series forecast
                forecast_list = point_forecast[0].tolist()
        
        # 3. Print the final clean JSON to stdout
        result = {
            "status": "success",
            "forecast": forecast_list
        }
        print(json.dumps(result))
        sys.exit(0)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": str(e)
        }
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
