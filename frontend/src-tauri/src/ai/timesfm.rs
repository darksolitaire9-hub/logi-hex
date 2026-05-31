#[cfg(not(test))]
use ort::session::{Session, builder::GraphOptimizationLevel};
#[cfg(not(test))]
use ort::value::Tensor;
#[cfg(not(test))]
use ndarray::Array2;
use std::path::PathBuf;

#[cfg(not(test))]
pub struct TimesFMEngine {
    session: Session,
}

#[cfg(not(test))]
impl TimesFMEngine {
    /// Loads the TimesFM 2.5 ONNX model from the specified file path.
    /// Note: ort::init() must be called BEFORE constructing this struct (done by AiStateManager).
    pub fn new(model_path: &PathBuf) -> Result<Self, String> {
        let session = Session::builder()
            .map_err(|e| format!("Failed to create ORT builder: {}", e))?
            .with_optimization_level(GraphOptimizationLevel::Level3)
            .map_err(|e| format!("Failed to set optimization: {}", e))?
            .with_intra_threads(4)
            .map_err(|e| format!("Failed to set threads: {}", e))?
            .commit_from_file(model_path)
            .map_err(|e| format!("Failed to load ONNX model at {:?}: {}", model_path, e))?;

        Ok(Self { session })
    }

    /// Predicts the `horizon` using the ONNX graph.
    /// Expects `history` to be padded/sliced appropriately before being passed in.
    pub fn predict(&mut self, history: &[f64], horizon: usize) -> Result<Vec<f64>, String> {
        if history.is_empty() {
            return Err("History cannot be empty".to_string());
        }

        let batch_size = 1;
        let context_len = history.len();

        // 1. Convert Rust `Vec<f64>` to an `ndarray` of `f32` (model precision)
        let mut past_values = Array2::<f32>::zeros((batch_size, context_len));
        for (i, &val) in history.iter().enumerate() {
            past_values[[0, i]] = val as f32;
        }

        // 2. Bind inputs. TimesFM 2.5 uses `past_values`.
        let tensor = Tensor::from_array(past_values)
            .map_err(|e| format!("Failed to create Tensor: {}", e))?;
        let inputs = ort::inputs!["past_values" => tensor];

        // 3. Execute Graph
        let outputs = self.session.run(inputs)
            .map_err(|e| format!("ONNX Inference error: {}", e))?;

        // 4. Extract `mean_predictions`
        let mean_tensor = outputs["mean_predictions"]
            .try_extract_tensor::<f32>()
            .map_err(|e| format!("Failed to extract mean_predictions from ONNX output: {}", e))?;

        // 5. Convert back to `Vec<f64>` mapping output predictions up to the required horizon
        let mut raw_values = Vec::new();
        for &val in mean_tensor.1.iter() {
            raw_values.push(val);
        }
        validate_and_collect_predictions(&raw_values, horizon)
    }
}

/// Validates predictions and collects them, converting from model precision f32 to domain f64.
/// Throws an error if any predictions are negative (physical constraint).
pub fn validate_and_collect_predictions(raw_values: &[f32], horizon: usize) -> Result<Vec<f64>, String> {
    if raw_values.is_empty() {
        return Err("ONNX output tensor is empty".to_string());
    }
    let mut predictions = Vec::with_capacity(horizon);
    for &val in raw_values.iter().take(horizon) {
        let val_f64 = val as f64;
        if val_f64 < 0.0 {
            return Err(format!("Negative prediction encountered in TimesFM model: {}", val_f64));
        }
        predictions.push(val_f64);
    }
    
    // If the model natively output fewer steps than the horizon, we pad with the last known value
    let last_val = *predictions.last().unwrap_or(&0.0);
    while predictions.len() < horizon {
        predictions.push(last_val);
    }

    Ok(predictions)
}

#[cfg(test)]
pub struct TimesFMEngine {
    _dummy: bool,
}

#[cfg(test)]
impl TimesFMEngine {
    pub fn new(model_path: &PathBuf) -> Result<Self, String> {
        if model_path.exists() {
            Ok(Self { _dummy: true })
        } else {
            Err("Mock model file does not exist".to_string())
        }
    }

    pub fn predict(&mut self, _history: &[f64], horizon: usize) -> Result<Vec<f64>, String> {
        Ok(vec![10.0; horizon]) // dummy mock forecast result
    }
}

#[cfg(test)]
mod timesfm_validation_tests {
    use super::*;

    #[test]
    fn test_validate_predictions_positive() {
        let raw = vec![1.5f32, 3.25, 5.5];
        let res = validate_and_collect_predictions(&raw, 3).unwrap();
        assert_eq!(res, vec![1.5, 3.25, 5.5]);
    }

    #[test]
    fn test_validate_predictions_negative() {
        let raw = vec![1.5f32, -0.5, 5.5];
        let res = validate_and_collect_predictions(&raw, 3);
        assert!(res.is_err());
        assert!(res.unwrap_err().contains("Negative prediction encountered in TimesFM model"));
    }

    #[test]
    fn test_validate_predictions_padding() {
        let raw = vec![1.5f32, 3.25];
        let res = validate_and_collect_predictions(&raw, 4).unwrap();
        assert_eq!(res, vec![1.5, 3.25, 3.25, 3.25]);
    }
}

