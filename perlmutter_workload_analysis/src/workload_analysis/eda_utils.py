"""
Utility functions for Exploratory Data Analysis (EDA).

This module provides common functions for data exploration, preprocessing,
and feature engineering for clustering tasks.
"""

import polars as pl
import pandas as pd
import numpy as np

from sklearn.preprocessing import StandardScaler


def describe_dataset(df, target_col=None):
    """
    Display basic information about a dataset.
    
    Parameters
    ----------
    df : polars.DataFrame or pandas.DataFrame
        The dataset to explore
    target_col : str, optional
        Name of the target/label column
        
    Returns
    -------
    None
        Prints information to the console
    """
    if isinstance(df, pd.DataFrame):
        df = pl.from_pandas(df)
    
    print(f"Dataset shape: {df.shape}")
    print("\nFirst 5 rows:")
    display(df.head())
    
    print("\nData Statistics:")
    display(df.describe())
    
    if target_col and target_col in df.columns:
        print(f"\n{target_col} Distribution:")
        display(df.group_by(target_col).agg(pl.count().alias('count')))



def standardize_features(df, exclude_cols=None):
    """
    Standardize numeric features in a DataFrame.
    
    Parameters
    ----------
    df : polars.DataFrame or pandas.DataFrame
        DataFrame containing features to standardize
    exclude_cols : list, optional
        List of column names to exclude from standardization
        
    Returns
    -------
    tuple
        (standardized_df, scaler) where standardized_df is a polars DataFrame
        and scaler is the fitted StandardScaler
    """
    is_pandas = isinstance(df, pd.DataFrame)
    if is_pandas:
        df = pl.from_pandas(df)
    
    if exclude_cols is None:
        exclude_cols = []
    
    # Select numeric columns for standardization
    numeric_cols = [col for col in df.columns if col not in exclude_cols]
    numeric_df = df.select(numeric_cols)
    
    # Convert to numpy for scikit-learn
    X = numeric_df.to_numpy()
    
    # Standardize
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Convert back to polars DataFrame
    scaled_df = pl.DataFrame(
        X_scaled,
        schema=[f"{col}_scaled" for col in numeric_cols]
    )
    
    return scaled_df, scaler