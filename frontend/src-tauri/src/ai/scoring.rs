pub struct ForecastScore {
    pub wape: Option<f64>,
    pub mase: Option<f64>,
    pub bias: Option<f64>,
}

/// Calculates WAPE, MASE, and Bias for a given forecast against actual holdout data.
/// 
/// `actual`: The true out-of-sample data points.
/// `forecast`: The predicted out-of-sample data points.
/// `train_actuals`: The historical in-sample training data (required for MASE naive denominator).
pub fn calculate_scores(actual: &[f64], forecast: &[f64], train_actuals: &[f64]) -> Result<ForecastScore, String> {
    if actual.len() != forecast.len() || actual.is_empty() {
        return Err("Actual and forecast slices must be the same non-zero length".to_string());
    }

    let n = actual.len() as f64;
    
    let mut sum_abs_error = 0.0;
    let mut sum_actual = 0.0;
    let mut sum_error = 0.0;

    for i in 0..actual.len() {
        let a = actual[i];
        let f = forecast[i];
        
        sum_abs_error += (a - f).abs();
        sum_actual += a.abs();
        sum_error += f - a; // Positive bias = over-forecast
    }

    // 1. WAPE
    let wape = if sum_actual == 0.0 {
        None // Mark unavailable if actuals are completely 0
    } else {
        Some(sum_abs_error / sum_actual)
    };

    // 2. Bias
    let bias = if sum_actual == 0.0 {
        None
    } else {
        Some(sum_error / sum_actual)
    };

    // 3. MASE
    let mut naive_mae_sum = 0.0;
    if train_actuals.len() > 1 {
        for i in 1..train_actuals.len() {
            naive_mae_sum += (train_actuals[i] - train_actuals[i-1]).abs();
        }
    }
    
    let naive_mae = if train_actuals.len() > 1 {
        naive_mae_sum / (train_actuals.len() - 1) as f64
    } else {
        0.0
    };

    let mae = sum_abs_error / n;

    let mase = if naive_mae == 0.0 {
        None // Mark unavailable if training data was perfectly flat (div by 0)
    } else {
        Some(mae / naive_mae)
    };

    Ok(ForecastScore {
        wape,
        mase,
        bias,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_perfect_forecast() {
        let actual = vec![10.0, 15.0, 20.0];
        let forecast = vec![10.0, 15.0, 20.0];
        let train = vec![5.0, 10.0];
        
        let score = calculate_scores(&actual, &forecast, &train).unwrap();
        assert_eq!(score.wape, Some(0.0));
        assert_eq!(score.bias, Some(0.0));
        assert_eq!(score.mase, Some(0.0));
    }

    #[test]
    fn test_intermittent_zero_demand_undefined() {
        let actual = vec![0.0, 0.0, 0.0];
        let forecast = vec![0.0, 0.0, 5.0];
        let train = vec![0.0, 0.0, 0.0, 0.0];
        
        let score = calculate_scores(&actual, &forecast, &train).unwrap();
        // Sum actual is 0. Metrics should be None instead of forcing 100% penalty
        assert_eq!(score.wape, None);
        assert_eq!(score.bias, None);
        assert_eq!(score.mase, None);
    }
}
