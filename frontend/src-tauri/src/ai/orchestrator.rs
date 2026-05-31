use crate::ai::scoring::calculate_scores;
use crate::ai::croston::croston_forecast;
use serde::Serialize;

#[derive(Serialize, Debug, Clone)]
pub struct EngineScore {
    pub engine_name: String,
    pub wape: Option<f64>,
    pub mase: Option<f64>,
    pub bias: Option<f64>,
}

/// The Baseline Cold-Start algorithm:
/// If history is too short for AI competition, use the last known non-zero demand.
pub fn last_known_demand_forecast(history: &[f64], horizon: usize) -> Vec<f64> {
    let mut last_demand = 0.0;
    for &val in history.iter().rev() {
        if val > 0.0 {
            last_demand = val;
            break;
        }
    }
    vec![last_demand; horizon]
}

/// Executes a walk-forward backtest simulation for all registered engines.
/// Returns a list of engine performance scores to be stored in the database.
pub fn run_backtest_simulation(model_dir: Option<std::path::PathBuf>, history: &[f64], horizon: usize, alpha: f64) -> Result<Vec<EngineScore>, String> {
    // 1. Cold Start Policy Enforcement
    // If history is less than (2 * horizon) + 1, it's impossible to properly train and test.
    let required_history = (horizon * 2).max(14); 
    if history.len() < required_history {
        // Return a baseline "score" so the DB knows only Baseline is viable
        return Ok(vec![EngineScore {
            engine_name: "Baseline_LastKnown".to_string(),
            wape: None,
            mase: None,
            bias: None,
        }]);
    }

    // 2. Prepare the Holdout Data (Simple single-split walk-forward)
    let split_idx = history.len() - horizon;
    let train_data = &history[0..split_idx];
    let actual_test_data = &history[split_idx..];

    let mut scores = Vec::new();

    // ----------------------------------------------------
    // Engine 1: Baseline (Last Known Demand)
    // ----------------------------------------------------
    let baseline_forecast = last_known_demand_forecast(train_data, horizon);
    if let Ok(score) = calculate_scores(actual_test_data, &baseline_forecast, train_data) {
        scores.push(EngineScore {
            engine_name: "Baseline_LastKnown".to_string(),
            wape: score.wape,
            mase: score.mase,
            bias: score.bias,
        });
    }

    // ----------------------------------------------------
    // Engine 2: Rust Native (Croston's Method)
    // ----------------------------------------------------
    let croston_forecast_vals = croston_forecast(train_data, horizon, alpha);
    if let Ok(score) = calculate_scores(actual_test_data, &croston_forecast_vals, train_data) {
        scores.push(EngineScore {
            engine_name: "Rust_Croston".to_string(),
            wape: score.wape,
            mase: score.mase,
            bias: score.bias,
        });
    }

    // ----------------------------------------------------
    // Engine 3: TimesFM ONNX (The AI Pack)
    // ----------------------------------------------------
    if let Some(mut path) = model_dir {
        path.push(crate::ai::TIMESFM_MODEL_FILENAME);
        if path.exists() {
            if let Ok(mut timesfm_engine) = crate::ai::timesfm::TimesFMEngine::new(&path) {
                if let Ok(timesfm_forecast_vals) = timesfm_engine.predict(train_data, horizon) {
                    if let Ok(score) = calculate_scores(actual_test_data, &timesfm_forecast_vals, train_data) {
                        scores.push(EngineScore {
                            engine_name: "TimesFM_2.5_ONNX".to_string(),
                            wape: score.wape,
                            mase: score.mase,
                            bias: score.bias,
                        });
                    }
                }
            }
        }
    }

    Ok(scores)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cold_start_policy_enforcement() {
        let history = vec![0.0, 5.0, 0.0];
        let horizon = 7;
        // History (3) is less than required (14). Must return Baseline only.
        let scores = run_backtest_simulation(None, &history, horizon, 0.2).unwrap();
        
        assert_eq!(scores.len(), 1);
        assert_eq!(scores[0].engine_name, "Baseline_LastKnown");
    }

    #[test]
    fn test_backtest_simulation() {
        // 20 days of data, 5 day horizon
        let history = vec![
            0.0, 10.0, 0.0, 0.0, 5.0, 0.0, 0.0, 10.0, 0.0, 0.0, 
            5.0, 0.0, 0.0, 10.0, 0.0, 0.0, 5.0, 0.0, 0.0, 10.0
        ];
        let horizon = 5;
        let scores = run_backtest_simulation(None, &history, horizon, 0.2).unwrap();
        
        assert_eq!(scores.len(), 2);
        
        let croston = scores.iter().find(|s| s.engine_name == "Rust_Croston").unwrap();
        assert!(croston.mase.is_some());
    }

    #[test]
    fn test_timesfm_eligibility_and_execution() {
        use std::fs::File;
        
        let mut temp_dir = std::env::temp_dir();
        temp_dir.push(format!("timesfm_test_{}", uuid::Uuid::new_v4()));
        std::fs::create_dir_all(&temp_dir).unwrap();
        
        let model_path = temp_dir.join(crate::ai::TIMESFM_MODEL_FILENAME);
        // Create dummy file
        File::create(&model_path).unwrap();

        // 20 days of data, 5 day horizon
        let history = vec![
            0.0, 10.0, 0.0, 0.0, 5.0, 0.0, 0.0, 10.0, 0.0, 0.0, 
            5.0, 0.0, 0.0, 10.0, 0.0, 0.0, 5.0, 0.0, 0.0, 10.0
        ];
        let horizon = 5;
        
        // 1. With the model file present in the directory, TimesFM should be executed (mocked) and scored
        let scores = run_backtest_simulation(Some(temp_dir.clone()), &history, horizon, 0.2).unwrap();
        let timesfm = scores.iter().find(|s| s.engine_name == "TimesFM_2.5_ONNX");
        assert!(timesfm.is_some(), "TimesFM_2.5_ONNX should be returned in scores when model file exists");
        
        // 2. Without the model file, TimesFM should be skipped
        std::fs::remove_file(&model_path).unwrap();
        let scores_empty = run_backtest_simulation(Some(temp_dir.clone()), &history, horizon, 0.2).unwrap();
        let timesfm_empty = scores_empty.iter().find(|s| s.engine_name == "TimesFM_2.5_ONNX");
        assert!(timesfm_empty.is_none(), "TimesFM_2.5_ONNX should not be returned when model file is absent");

        // Clean up directory
        std::fs::remove_dir(temp_dir).unwrap();
    }
}
