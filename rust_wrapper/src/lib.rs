use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use scorecard_to_pdf::{Language, Return};

use wca_scorecards_lib::*;

fn blank_scorecard(competition: &str) -> Vec<u8>{
    let blank_return = scorecard_to_pdf::blank_scorecard_page(competition, &Language::english());
    let blank_scorecard = match blank_return {
        Return::Pdf(b) => b,
        _ => unreachable!()
    };
    blank_scorecard
}

#[pyfunction]
fn blank_scorecards(competition: &str) -> PyResult<Vec<u8>> {
    Ok(blank_scorecard(competition as &str))
}

#[pyfunction]
fn anker_scorecards(groups_csv: String, limit_csv: Option<String>, competition: &str, no_stages: u32, per_stage: u32, sort_by_name: bool) -> PyResult<Vec<u8>> {
    Ok(round_1_scorecards_in_memory_for_python(groups_csv as String, limit_csv as Option<String>, competition as &str, no_stages as u32, per_stage as u32, sort_by_name as bool))
}

#[pymodule]
fn anker_scorecards_python(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(anker_scorecards, m)?)?;
    m.add_function(wrap_pyfunction!(blank_scorecards, m)?)?;

    Ok(())
}