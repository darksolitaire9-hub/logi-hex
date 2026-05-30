import sys
import json
import argparse
import os
import contextlib

def main():
    parser = argparse.ArgumentParser(description="Logi-Hex Hybrid Forecasting Sidecar")
    parser.add_argument("--history", type=str, required=True, help="JSON string of historical data points (list of floats)")
    parser.add_argument("--horizon", type=int, default=30, help="Number of future points to predict")
    
    args = parser.parse_args()
    
    try:
        # 1. Parse historical data
        history_data = json.loads(args.history)
        if not isinstance(history_data, list):
            raise ValueError("History must be a JSON list of numbers")
            
        history = [float(x) for x in history_data]
        
        if not history:
            history = [0.0]
            
        n_days = len(history)
        model_used = ""
        forecast_list = []
        
        # We redirect stdout and stderr to devnull to prevent polluting JSON
        with open(os.devnull, 'w') as devnull:
            with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
                
                # BRANCH A & B: Cold Start / Low Data (< 14 days) -> Pure Python Math Fallback
                # (Replacing StatsForecast dependency due to Scipy build failures on Windows Python 3.14)
                if n_days < 14:
                    if n_days < 7:
                        # Historic Average
                        model_used = "MathFallback:HistoricAverage"
                        avg = sum(history) / n_days if n_days > 0 else 0.0
                        forecast_list = [avg] * args.horizon
                    else:
                        # Seasonal Naive (7-day season)
                        model_used = "MathFallback:SeasonalNaive"
                        season = history[-7:]
                        forecast_list = []
                        for i in range(args.horizon):
                            forecast_list.append(season[i % 7])
                    
                    
                # BRANCH C: Mature Data (>= 14 days) -> TimesFM
                else:
                    model_used = "TimesFM-1.0-200m"
                    import timesfm
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
                    freq = [0]
                    point_forecast, _ = tfm.forecast(forecast_input, freq=freq)
                    forecast_list = point_forecast[0].tolist()
        
        # 3. Print the final clean JSON to stdout
        result = {
            "status": "success",
            "model_used": model_used,
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
