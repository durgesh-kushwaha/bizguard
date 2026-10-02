"""
Forecasting page for BizGuard.

Displays ML model training, evaluation, and demand forecasting.
All metrics are computed from actual model output — never hardcoded.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from src.utils.formatting import format_number

ML_PIPELINE_REVISION = 3


def render():
    """Render the Forecasting page."""
    st.title("🔮 Demand Forecast")
    st.caption("Train and validate demand models, then forecast daily unit totals.")
    
    if st.session_state.get("cleaned_df") is None:
        st.info("👈 Load and clean your data in the **Data Explorer** page first.")
        return
    
    df = st.session_state.cleaned_df

    if st.session_state.get("ml_pipeline_revision") != ML_PIPELINE_REVISION:
        for key in (
            "models", "model_evaluations", "X_test", "y_test",
            "preprocessing_summary", "feature_cols", "ml_df", "current_forecast",
        ):
            st.session_state[key] = None
        st.session_state.ml_pipeline_revision = ML_PIPELINE_REVISION
        st.info("Forecasting was updated. Previous models and saved forecasts were cleared.")
    
    # ML Pipeline tabs
    tab_train, tab_evaluate, tab_forecast = st.tabs([
        "🏋️ Train Models", "📊 Evaluate", "📈 Forecast"
    ])
    
    with tab_train:
        _render_training(df)
    
    with tab_evaluate:
        _render_evaluation()
    
    with tab_forecast:
        _render_forecast(df)


def _render_training(df: pd.DataFrame):
    """Render model training section."""
    st.markdown("### Transaction Model Training")
    
    st.markdown("""
    Transaction-level models are evaluated on the latest 20% of dated records.
    The forecast tab separately aggregates units by calendar day and selects a
    model using rolling-origin backtests against a weekly seasonal baseline.
    """)
    
    if st.session_state.get("models") is not None:
        st.success("✅ Models are already trained. Go to Evaluate or Forecast tabs.")
        if st.button("🔄 Retrain Models"):
            st.session_state.models = None
            st.session_state.model_evaluations = None
            st.rerun()
        return
    
    st.markdown("---")
    
    if st.button("🚀 Train ML Models", type="primary"):
        _run_training_pipeline(df)


def _run_training_pipeline(df: pd.DataFrame):
    """Execute the full ML training pipeline."""
    progress = st.progress(0, text="Starting ML pipeline...")
    
    try:
        # Step 1: Feature Engineering
        progress.progress(10, text="Step 1/5: Feature engineering...")
        from src.data.feature_engineering import prepare_ml_features
        ml_df = prepare_ml_features(df)
        st.session_state.ml_df = ml_df
        
        # Step 2: Prepare features
        progress.progress(25, text="Step 2/5: Preparing features...")
        from src.ml.preprocessing import prepare_features, split_data, get_preprocessing_summary
        X, y, feature_cols = prepare_features(ml_df)
        st.session_state.feature_cols = feature_cols
        
        # Step 3: Split data
        progress.progress(40, text="Step 3/5: Splitting train/test...")
        dates = ml_df.loc[X.index, "date"] if "date" in ml_df.columns else None
        X_train, X_test, y_train, y_test = split_data(X, y, dates=dates)
        
        # Store for evaluation
        st.session_state.X_test = X_test
        st.session_state.y_test = y_test
        st.session_state.preprocessing_summary = get_preprocessing_summary(
            X_train, X_test, y_train, y_test, feature_cols
        )
        
        # Step 4: Train models
        progress.progress(60, text="Step 4/5: Training baseline and ensemble models...")
        from src.ml.train import train_all_models
        models = train_all_models(X_train, y_train)
        st.session_state.models = models
        
        # Step 5: Evaluate models
        progress.progress(80, text="Step 5/5: Evaluating models...")
        from src.ml.evaluate import evaluate_model
        evaluations = {}
        for model_type, (model, info) in models.items():
            evaluations[info["model_name"]] = evaluate_model(model, X_test, y_test)
        st.session_state.model_evaluations = evaluations
        
        progress.progress(100, text="✅ Training complete!")
        
        # Show summary
        summary = st.session_state.preprocessing_summary
        st.success(
            f"Models trained successfully on {summary['training_samples']:,} samples "
            f"with {summary['num_features']} features."
        )
        st.rerun()
    
    except Exception as e:
        progress.empty()
        st.error(f"❌ Training failed: {e}")
        st.markdown("**Possible causes:**")
        st.markdown("- Not enough data (need at least 50 rows after feature engineering)")
        st.markdown("- Missing required columns")
        st.markdown("- Data quality issues")


def _render_evaluation():
    """Render model evaluation section."""
    st.markdown("### Model Evaluation")
    
    if st.session_state.get("model_evaluations") is None:
        st.info("👈 Train the models first in the **Train Models** tab.")
        return
    
    evaluations = st.session_state.model_evaluations
    models = st.session_state.models
    summary = st.session_state.get("preprocessing_summary", {})
    
    # Preprocessing summary
    with st.expander("📋 Preprocessing Summary", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Samples", format_number(summary.get("total_samples", 0)))
        with col2:
            st.metric("Training Samples", format_number(summary.get("training_samples", 0)))
        with col3:
            st.metric("Testing Samples", format_number(summary.get("testing_samples", 0)))
        with col4:
            st.metric("Features Used", format_number(summary.get("num_features", 0)))
        
        st.markdown("**Features:**")
        st.markdown(", ".join(f"`{f}`" for f in summary.get("feature_names", [])))
    
    # Model comparison table
    st.markdown("#### Model Comparison")
    from src.ml.evaluate import compare_models, get_evaluation_explanation
    comparison = compare_models(evaluations)
    st.dataframe(comparison, use_container_width=True, hide_index=True)
    
    st.markdown("""
    **Metric Interpretation:**
    - **MAE** (Mean Absolute Error): Average prediction error in units. Lower is better.
    - **RMSE** (Root Mean Squared Error): Penalizes large errors more. Lower is better.
    - **R²** (R-squared): Proportion of variance explained. 1.0 = perfect, 0.0 = predicts mean.
    """)
    
    # Per-model details
    for model_name, eval_result in evaluations.items():
        model_type = None
        model_info = None
        for mt, (m, info) in models.items():
            if info["model_name"] == model_name:
                model_type = mt
                model_info = info
                break
        
        with st.expander(f"📊 {model_name} Details"):
            # Model description
            if model_info:
                st.markdown(f"*{model_info.get('description', '')}*")
                st.markdown(f"**Training time:** {model_info.get('training_time_seconds', 0)}s")
            
            # Explanation
            explanation = get_evaluation_explanation(eval_result)
            st.markdown(explanation)
            
            # Actual vs Predicted chart
            st.markdown("##### Actual vs Predicted")
            sample_size = min(200, len(eval_result["actuals"]))
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                y=eval_result["actuals"][:sample_size],
                mode="markers", name="Actual",
                marker=dict(color="#2563eb", size=5),
            ))
            fig.add_trace(go.Scatter(
                y=eval_result["predictions"][:sample_size],
                mode="markers", name="Predicted",
                marker=dict(color="#dc2626", size=5),
            ))
            fig.update_layout(
                height=300, xaxis_title="Sample", yaxis_title="Quantity",
                hovermode="x unified",
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Feature importance (for Random Forest)
            if model_info and "feature_importance" in model_info:
                st.markdown("##### Feature Importance")
                st.caption("Which features most influence the model's predictions.")
                importance = model_info["feature_importance"]
                imp_df = pd.DataFrame({
                    "Feature": list(importance.keys())[:10],
                    "Importance": list(importance.values())[:10],
                })
                fig = px.bar(
                    imp_df, x="Importance", y="Feature",
                    orientation="h", color_discrete_sequence=["#7c3aed"],
                )
                fig.update_layout(
                    height=300, yaxis=dict(autorange="reversed"),
                )
                st.plotly_chart(fig, use_container_width=True)


def _render_forecast(df: pd.DataFrame):
    """Render demand forecast section."""
    st.markdown("### Demand Forecast")

    st.caption("Daily-demand engine v3 · Models are checked against chronological holdouts and a weekly baseline.")
    # Forecast controls
    col1, col2 = st.columns(2)

    with col1:
        products = ["All Products"] + sorted(df["product_id"].unique().tolist()) if "product_id" in df.columns else ["All Products"]
        selected_product = st.selectbox("Product", products)
    with col2:
        forecast_days = st.slider("Forecast Period (days)", 7, 90, 30)

    if st.button("📈 Generate Forecast", type="primary"):
        with st.spinner("Generating forecast..."):
            try:
                from src.ml.demand_forecast import forecast_daily_demand

                product_id = None if selected_product == "All Products" else selected_product
                forecast = forecast_daily_demand(
                    df, periods=forecast_days, product_id=product_id,
                )
                st.session_state.current_forecast = forecast
                st.rerun()
            except ValueError as e:
                st.warning(str(e))
            except Exception as e:
                st.error(f"Forecast could not be generated: {e}")

    # Display forecast if available
    if st.session_state.get("current_forecast") is not None:
        forecast = st.session_state.current_forecast
        if forecast.get("forecast_version") != 3:
            st.session_state.current_forecast = None
            st.info("This saved forecast used the previous model. Generate a new forecast to refresh it.")
            return

        st.markdown("---")
        st.markdown(f"#### Forecast Results — {forecast['model_name']} · Daily units")

        # KPI cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Forecast Period", f"{forecast['periods']} days")
        with col2:
            st.metric("Total Predicted", format_number(forecast["total_predicted"]))
        with col3:
            st.metric("Avg Daily", format_number(forecast["avg_daily_predicted"], 1))
        with col4:
            product_label = forecast.get("product_id", "All Products") or "All Products"
            st.metric("Product", product_label)

        if forecast["beats_baseline"]:
            st.success(
                f"Chronological backtest WAPE: {forecast['backtest_wape']:.1f}% "
                f"versus {forecast['baseline_wape']:.1f}% for the seasonal-naive baseline."
            )
        else:
            st.info(
                f"The seasonal-naive baseline performed best in the chronological backtest "
                f"(WAPE {forecast['baseline_wape']:.1f}%). The forecast uses that baseline; "
                f"the trained models did not improve on it."
            )

        # Forecast chart
        st.markdown("#### Historical + Forecast")
        hist_daily = forecast["history"].tail(90)
        fig = go.Figure()

        # Historical
        fig.add_trace(go.Scatter(
            x=hist_daily.index, y=hist_daily.values,
            mode="lines", name="Historical",
            line=dict(color="#2563eb", width=2),
        ))

        # Forecast
        forecast_dates = forecast["dates"]
        forecast_values = forecast["predictions"]

        fig.add_trace(go.Scatter(
            x=forecast_dates, y=forecast_values,
            mode="lines+markers", name="Forecast",
            line=dict(color="#dc2626", width=2, dash="dash"),
            marker=dict(size=4),
        ))
        
        fig.update_layout(
            height=400,
            xaxis_title="Date",
            yaxis_title="Quantity (units)",
            hovermode="x unified",
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Model info
        with st.expander("ℹ️ Model Information"):
            st.markdown(f"**Backtest MAE:** {forecast['backtest_mae']:.2f} units per day")
            st.markdown(f"**Backtest WAPE:** {forecast['backtest_wape']:.1f}%")
            st.markdown(f"**Seasonal-naive WAPE:** {forecast['baseline_wape']:.1f}%")
            st.markdown(f"**Validation:** three rolling-origin folds, {forecast['validation_days']} days each")
            st.markdown(f"**Model:** {forecast['model_name']}")
            st.info(
                "Historical validation is not a guarantee of future accuracy. Unexpected promotions, "
                "stockouts, price changes, and market shifts are not known to this model."
            )
