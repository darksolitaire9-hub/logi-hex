/// An implementation of Croston's Method for intermittent demand forecasting.
/// This method separately smooths the demand size and the inter-demand intervals.
pub fn croston_forecast(history: &[f64], horizon: usize, alpha: f64) -> Vec<f64> {
    if history.is_empty() {
        return vec![0.0; horizon];
    }

    // Initialize state
    // To initialize, find the first non-zero demand to set starting z and p.
    let mut z = 0.0; // Demand size
    let mut p = 1.0; // Inter-demand interval
    let mut q = 1.0; // Periods since last demand

    // Find the first non-zero value to seed the state
    for (i, &val) in history.iter().enumerate() {
        if val > 0.0 {
            z = val;
            p = (i as f64) + 1.0;
            break;
        }
    }

    // If entire history is zeros, return zeros.
    if z == 0.0 {
        return vec![0.0; horizon];
    }

    // Run Croston's smoothing over the historical data
    for &y in history {
        if y > 0.0 {
            // Demand occurred
            z = alpha * y + (1.0 - alpha) * z;
            p = alpha * q + (1.0 - alpha) * p;
            q = 1.0;
        } else {
            // No demand
            q += 1.0;
        }
    }

    // The forecast is simply the smoothed demand size divided by the smoothed interval.
    // Croston assumes a flat forecast moving forward (naive random walk approach).
    let forecast_val = if p > 0.0 { z / p } else { 0.0 };

    vec![forecast_val; horizon]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_croston_sparse() {
        let history = vec![0.0, 10.0, 0.0, 0.0, 10.0, 0.0, 0.0];
        let forecast = croston_forecast(&history, 5, 0.1);
        
        assert_eq!(forecast.len(), 5);
        // It shouldn't crash or return NaN
        assert!(forecast[0] > 0.0);
    }

    #[test]
    fn test_croston_all_zeros() {
        let history = vec![0.0, 0.0, 0.0];
        let forecast = croston_forecast(&history, 3, 0.2);
        assert_eq!(forecast, vec![0.0, 0.0, 0.0]);
    }
}
