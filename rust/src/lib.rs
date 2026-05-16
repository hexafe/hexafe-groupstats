use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use rand::rngs::StdRng;
use rand::{Rng, SeedableRng};
use statrs::distribution::{ContinuousCDF, StudentsT};

type PairwiseRow = (
    String,
    String,
    String,
    Option<f64>,
    Option<f64>,
    Option<f64>,
    bool,
);

fn mean(values: &[f64]) -> Option<f64> {
    if values.is_empty() {
        return None;
    }
    Some(values.iter().sum::<f64>() / values.len() as f64)
}

fn variance(values: &[f64], mean_value: f64) -> Option<f64> {
    if values.len() < 2 {
        return None;
    }
    let sum_sq = values
        .iter()
        .map(|value| {
            let centered = value - mean_value;
            centered * centered
        })
        .sum::<f64>();
    Some(sum_sq / (values.len() as f64 - 1.0))
}

fn stddev(values: &[f64], mean_value: f64) -> Option<f64> {
    variance(values, mean_value).map(f64::sqrt)
}

fn cohen_d_from_stats(
    mean_a: f64,
    std_a: f64,
    n_a: usize,
    mean_b: f64,
    std_b: f64,
    n_b: usize,
) -> Option<f64> {
    if n_a < 2 || n_b < 2 {
        return None;
    }
    let pooled_den = (n_a + n_b - 2) as f64;
    if pooled_den <= 0.0 {
        return None;
    }
    let pooled =
        (((n_a - 1) as f64 * std_a.powi(2)) + ((n_b - 1) as f64 * std_b.powi(2))) / pooled_den;
    if pooled <= 0.0 || !pooled.is_finite() {
        return None;
    }
    Some((mean_a - mean_b) / pooled.sqrt())
}

fn ttest_from_stats(
    mean_a: f64,
    std_a: f64,
    n_a: usize,
    mean_b: f64,
    std_b: f64,
    n_b: usize,
    equal_var: bool,
) -> Option<f64> {
    if n_a < 2 || n_b < 2 {
        return None;
    }
    let var_a = std_a.powi(2);
    let var_b = std_b.powi(2);
    let (standard_error, degrees_freedom) = if equal_var {
        let pooled_den = (n_a + n_b - 2) as f64;
        if pooled_den <= 0.0 {
            return None;
        }
        let pooled = (((n_a - 1) as f64 * var_a) + ((n_b - 1) as f64 * var_b)) / pooled_den;
        (
            (pooled * ((1.0 / n_a as f64) + (1.0 / n_b as f64))).sqrt(),
            pooled_den,
        )
    } else {
        let se_sq = (var_a / n_a as f64) + (var_b / n_b as f64);
        let denom = ((var_a / n_a as f64).powi(2) / (n_a as f64 - 1.0))
            + ((var_b / n_b as f64).powi(2) / (n_b as f64 - 1.0));
        if denom <= 0.0 {
            return None;
        }
        (se_sq.sqrt(), se_sq.powi(2) / denom)
    };
    if standard_error <= 0.0 || !standard_error.is_finite() || degrees_freedom <= 0.0 {
        return None;
    }
    let statistic = (mean_a - mean_b) / standard_error;
    let distribution = StudentsT::new(0.0, 1.0, degrees_freedom).ok()?;
    let tail = 1.0 - distribution.cdf(statistic.abs());
    let p_value = (2.0 * tail).clamp(0.0, 1.0);
    if p_value.is_finite() {
        Some(p_value)
    } else {
        None
    }
}

fn normalize_correction_method(method: &str) -> String {
    match method.trim().to_lowercase().replace('-', "_").as_str() {
        "holm_bonferroni" => "holm".to_string(),
        "benjamini_hochberg" | "fdr_bh" => "bh".to_string(),
        value => value.to_string(),
    }
}

fn adjust_pvalues(p_values: &[Option<f64>], method: &str) -> PyResult<Vec<Option<f64>>> {
    let mut indexed = p_values
        .iter()
        .enumerate()
        .filter_map(|(index, value)| value.filter(|p| p.is_finite()).map(|p| (index, p)))
        .collect::<Vec<_>>();
    let mut adjusted = vec![None; p_values.len()];
    if indexed.is_empty() {
        return Ok(adjusted);
    }
    indexed.sort_by(|left, right| left.1.partial_cmp(&right.1).unwrap());
    let count = indexed.len();
    match normalize_correction_method(method).as_str() {
        "holm" => {
            let mut running_max = 0.0;
            for (rank, (original_index, p_value)) in indexed.iter().enumerate() {
                let corrected = (p_value * (count - rank) as f64).min(1.0);
                if corrected > running_max {
                    running_max = corrected;
                }
                adjusted[*original_index] = Some(running_max);
            }
        }
        "bh" => {
            let mut running_min = 1.0;
            for (reverse_rank, (original_index, p_value)) in indexed.iter().rev().enumerate() {
                let rank = count - reverse_rank;
                let corrected = (p_value * count as f64 / rank as f64).min(1.0);
                if corrected < running_min {
                    running_min = corrected;
                }
                adjusted[*original_index] = Some(running_min);
            }
        }
        _ => {
            return Err(PyValueError::new_err(format!(
                "Unsupported correction method: {method}"
            )))
        }
    }
    Ok(adjusted)
}

fn percentile(sorted_values: &[f64], percentile_value: f64) -> Option<f64> {
    if sorted_values.is_empty() {
        return None;
    }
    if sorted_values.len() == 1 {
        return Some(sorted_values[0]);
    }
    let rank = (percentile_value / 100.0) * (sorted_values.len() - 1) as f64;
    let lower = rank.floor() as usize;
    let upper = rank.ceil() as usize;
    if lower == upper {
        return Some(sorted_values[lower]);
    }
    let weight = rank - lower as f64;
    Some(sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight)
}

#[pyfunction]
fn compute_pairwise_batch(
    labels: Vec<String>,
    groups: Vec<Vec<f64>>,
    alpha: f64,
    correction_method: String,
    non_parametric: bool,
    equal_var: bool,
) -> PyResult<Vec<PairwiseRow>> {
    if non_parametric {
        return Err(PyValueError::new_err(
            "non-parametric pairwise fallback required",
        ));
    }
    if labels.len() != groups.len() {
        return Err(PyValueError::new_err(
            "labels and groups must have the same length",
        ));
    }

    let means = groups.iter().map(|group| mean(group)).collect::<Vec<_>>();
    let stds = groups
        .iter()
        .zip(means.iter())
        .map(|(group, mean_value)| mean_value.and_then(|value| stddev(group, value)))
        .collect::<Vec<_>>();

    let mut raw_rows: Vec<PairwiseRow> = Vec::new();
    let mut raw_p_values: Vec<Option<f64>> = Vec::new();
    for left in 0..groups.len() {
        for right in (left + 1)..groups.len() {
            let test_name = if equal_var {
                "Student t-test"
            } else {
                "Welch t-test"
            }
            .to_string();
            let p_value = match (means[left], stds[left], means[right], stds[right]) {
                (Some(mean_a), Some(std_a), Some(mean_b), Some(std_b)) => ttest_from_stats(
                    mean_a,
                    std_a,
                    groups[left].len(),
                    mean_b,
                    std_b,
                    groups[right].len(),
                    equal_var,
                ),
                _ => None,
            };
            let effect_size = match (means[left], stds[left], means[right], stds[right]) {
                (Some(mean_a), Some(std_a), Some(mean_b), Some(std_b)) => cohen_d_from_stats(
                    mean_a,
                    std_a,
                    groups[left].len(),
                    mean_b,
                    std_b,
                    groups[right].len(),
                ),
                _ => None,
            };
            raw_p_values.push(p_value);
            raw_rows.push((
                labels[left].clone(),
                labels[right].clone(),
                test_name,
                p_value,
                effect_size,
                None,
                false,
            ));
        }
    }

    let adjusted = adjust_pvalues(&raw_p_values, &correction_method)?;
    Ok(raw_rows
        .into_iter()
        .zip(adjusted)
        .map(|(row, adjusted_p_value)| {
            (
                row.0,
                row.1,
                row.2,
                row.3,
                row.4,
                adjusted_p_value,
                adjusted_p_value.is_some_and(|value| value < alpha),
            )
        })
        .collect())
}

#[pyfunction]
fn bootstrap_percentile_ci(
    effect_kernel: String,
    groups: Vec<Vec<f64>>,
    level: f64,
    iterations: usize,
    seed: u64,
) -> PyResult<Option<(f64, f64)>> {
    if effect_kernel != "cohen_d" || groups.len() != 2 || groups[0].len() < 2 || groups[1].len() < 2
    {
        return Ok(None);
    }
    let mut rng = StdRng::seed_from_u64(seed);
    let resolved_iterations = iterations.max(1);
    let mut estimates = Vec::with_capacity(resolved_iterations);
    for _ in 0..resolved_iterations {
        let left = (0..groups[0].len())
            .map(|_| groups[0][rng.gen_range(0..groups[0].len())])
            .collect::<Vec<_>>();
        let right = (0..groups[1].len())
            .map(|_| groups[1][rng.gen_range(0..groups[1].len())])
            .collect::<Vec<_>>();
        let left_mean = match mean(&left) {
            Some(value) => value,
            None => continue,
        };
        let right_mean = match mean(&right) {
            Some(value) => value,
            None => continue,
        };
        let left_std = match stddev(&left, left_mean) {
            Some(value) => value,
            None => continue,
        };
        let right_std = match stddev(&right, right_mean) {
            Some(value) => value,
            None => continue,
        };
        if let Some(value) = cohen_d_from_stats(
            left_mean,
            left_std,
            left.len(),
            right_mean,
            right_std,
            right.len(),
        ) {
            if value.is_finite() {
                estimates.push(value);
            }
        }
    }
    if estimates.is_empty() {
        return Ok(None);
    }
    estimates.sort_by(|left, right| left.partial_cmp(right).unwrap());
    let lower_q = ((1.0 - level) / 2.0) * 100.0;
    let upper_q = (1.0 - (1.0 - level) / 2.0) * 100.0;
    Ok(
        match (
            percentile(&estimates, lower_q),
            percentile(&estimates, upper_q),
        ) {
            (Some(lower), Some(upper)) => Some((lower, upper)),
            _ => None,
        },
    )
}

#[pyfunction]
fn bootstrap_percentile_ci_batch(
    effect_kernel: String,
    groups: Vec<Vec<f64>>,
    pairs: Vec<(usize, usize)>,
    level: f64,
    iterations: usize,
    seed: u64,
) -> PyResult<Vec<Option<(f64, f64)>>> {
    let mut output = Vec::with_capacity(pairs.len());
    for (offset, (left, right)) in pairs.into_iter().enumerate() {
        if left >= groups.len() || right >= groups.len() {
            output.push(None);
            continue;
        }
        output.push(bootstrap_percentile_ci(
            effect_kernel.clone(),
            vec![groups[left].clone(), groups[right].clone()],
            level,
            iterations,
            seed + offset as u64,
        )?);
    }
    Ok(output)
}

#[pymodule]
fn _hexafe_groupstats_native(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(compute_pairwise_batch, module)?)?;
    module.add_function(wrap_pyfunction!(bootstrap_percentile_ci, module)?)?;
    module.add_function(wrap_pyfunction!(bootstrap_percentile_ci_batch, module)?)?;
    Ok(())
}
