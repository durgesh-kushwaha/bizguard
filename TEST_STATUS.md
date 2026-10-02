# TEST STATUS — BizGuard

**Last Updated:** 2026-10-02

## Summary
| Suite | Status | Pass | Fail | Skip |
|-------|--------|------|------|------|
| Data | ✅ PASSED | 15 | 0 | 0 |
| BDA/Spark | ✅ PASSED | 3 | 0 | 0 |
| Decisions | ✅ PASSED | 11 | 0 | 0 |
| ML | ✅ PASSED | 8 | 0 | 0 |
| Utils/DB | ✅ PASSED | 7 | 0 | 0 |
| **Total** | **✅ ALL PASS** | **44** | **0** | **0** |

## Last Test Run
```
python -m pytest tests/ -q
44 passed in 11.68s
Date: 2026-10-02
```

## Test Details

### Data Tests (test_data.py)
- ✅ TestDataLoader::test_load_sample_data
- ✅ TestDataLoader::test_load_csv_from_path
- ✅ TestDataLoader::test_load_invalid_file
- ✅ TestDataValidator::test_validate_valid_data
- ✅ TestDataValidator::test_validate_missing_columns
- ✅ TestDataValidator::test_validate_negative_values
- ✅ TestDataValidator::test_validate_duplicates
- ✅ TestDataCleaner::test_clean_valid_data
- ✅ TestDataCleaner::test_clean_removes_duplicates
- ✅ TestDataCleaner::test_derived_columns_computed

### Decision Tests (test_decisions.py)
- ✅ TestPricingSimulator::test_simulate_pricing
- ✅ TestPricingSimulator::test_pricing_price_decrease
- ✅ TestPricingSimulator::test_pricing_unknown_product
- ✅ TestPricingSimulator::test_price_elasticity_estimation
- ✅ TestInventorySimulator::test_simulate_inventory
- ✅ TestInventorySimulator::test_inventory_zero_purchase
- ✅ TestMarketingSimulator::test_simulate_marketing
- ✅ TestMarketingSimulator::test_marketing_by_category
- ✅ TestMarketingSimulator::test_historical_roas
- ✅ TestDecisionEngine::test_run_pricing_decision
- ✅ TestDecisionEngine::test_decision_contract_fields

### ML Tests (test_ml.py)
- ✅ TestFeatureEngineering::test_temporal_features
- ✅ TestFeatureEngineering::test_lag_features
- ✅ TestFeatureEngineering::test_rolling_features
- ✅ TestFeatureEngineering::test_full_pipeline
- ✅ TestMLTraining::test_train_linear_regression
- ✅ TestMLTraining::test_train_random_forest
- ✅ TestMLEvaluation::test_evaluate_model
- ✅ TestMLEvaluation::test_compare_models

### Utility/DB Tests (test_utils.py)
- ✅ TestFormatting::test_format_currency
- ✅ TestFormatting::test_format_number
- ✅ TestFormatting::test_format_percentage
- ✅ TestFormatting::test_format_currency_large
- ✅ TestDatabase::test_init_database
- ✅ TestDatabase::test_save_and_retrieve_decision
- ✅ TestDatabase::test_delete_decision

### BDA Tests (test_bda.py)
- ✅ Empty-data KPI handling
- ✅ Order-based average order value and profit margin
- ✅ PySpark cleaning and derived revenue/profit (PySpark 4.2.0, Java 17)

## Test Commands
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific suites
python -m pytest tests/test_data.py -v
python -m pytest tests/test_ml.py -v
python -m pytest tests/test_decisions.py -v
python -m pytest tests/test_utils.py -v
```
