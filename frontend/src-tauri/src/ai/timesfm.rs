use ort::session::{Session, builder::GraphOptimizationLevel};
use ort::value::Tensor;
use ndarray::Array2;
use std::path::PathBuf;

pub struct TimesFMEngine {
    session: Session,
}

impl TimesFMEngine {
    /// Loads the TimesFM 2.5 ONNX model from the specified file path.
    pub fn new(model_path: &PathBuf) -> Result<Self, String> {
        // Initialize ORT. It's safe to call this multiple times, it only inits once.
        let _ = ort::init()
            .with_name("logi-hex")
            .commit(); // Ignore Error if already initialized

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
    pub fn predict(&self, history: &[f64], horizon: usize) -> Result<Vec<f64>, String> {
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
        let mut predictions = Vec::with_capacity(horizon);
        for &val in mean_tensor.1.iter().take(horizon) {
            let val_f64 = val as f64;
            // Zero-floor the output since physical inventory cannot drop below zero
            predictions.push(if val_f64 < 0.0 { 0.0 } else { val_f64 });
        }

        // If the model natively output fewer steps than the horizon, we pad with the last known value
        let mut last_val = *predictions.last().unwrap_or(&0.0);
        while predictions.len() < horizon {
            predictions.push(last_val);
        }

        Ok(predictions)
    }
}
