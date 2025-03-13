"""
Utility functions for visualizing clustering results.

This module provides functions for visualizing clusters in 2D and 3D
using various dimensionality reduction techniques.
"""

import numpy as np
import polars as pl
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.manifold import MDS, TSNE
import plotly.graph_objs as go
import plotly.offline as pyo


def reduce_dimensions(X, method="pca", n_components=2, **kwargs):
    """
    Reduce the dimensionality of the data.
    
    Parameters
    ----------
    X : numpy.ndarray
        Input data to reduce
    method : str, optional
        Dimensionality reduction method ("pca", "mds", "tsne")
    n_components : int, optional
        Number of components to reduce to
    **kwargs : dict
        Additional parameters for the dimensionality reduction method
        
    Returns
    -------
    numpy.ndarray
        Reduced data
    """
    if method.lower() == "pca":
        reducer = PCA(n_components=n_components, **kwargs)
    elif method.lower() == "mds":
        reducer = MDS(n_components=n_components, **kwargs)
    elif method.lower() == "tsne":
        reducer = TSNE(n_components=n_components, **kwargs)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return reducer.fit_transform(X)


def plot_clusters_plotly(X_reduced, labels, centers=None, point_labels=None, title=None):
    """
    Plot clusters using Plotly for interactive visualization.
    
    Parameters
    ----------
    X_reduced : numpy.ndarray
        Reduced data (2D or 3D)
    labels : numpy.ndarray
        Cluster labels
    centers : numpy.ndarray, optional
        Cluster centers in reduced space
    point_labels : list or array, optional
        Labels for individual points (e.g., sample names)
    title : str, optional
        Title for the plot
        
    Returns
    -------
    plotly.graph_objs._figure.Figure
        The generated interactive plot
    """
    n_dims = X_reduced.shape[1]
    if n_dims not in (2, 3):
        raise ValueError("Data must be reduced to 2 or 3 dimensions")
    
    unique_labels = np.unique(labels)
    n_clusters = len(unique_labels)
    
    # Generate a colorful palette
    colors = [f'rgb({int(r*255)},{int(g*255)},{int(b*255)})' 
              for r, g, b in plt.cm.rainbow(np.linspace(0, 1, n_clusters))[:, :3]]
    
    traces = []
    
    for i, label in enumerate(unique_labels):
        mask = labels == label
        
        if label == -1:  # Noise points in DBSCAN
            color = 'grey'
            name = 'Noise'
        else:
            color = colors[i]
            name = f'Cluster {label}'
        
        # Get the indices where mask is True
        indices = np.where(mask)[0]
        
        # Prepare hover text (properly handling lists)
        hover_text = None
        if point_labels is not None:
            hover_text = [point_labels[idx] for idx in indices]
        
        if n_dims == 2:
            trace = go.Scatter(
                x=X_reduced[mask, 0],
                y=X_reduced[mask, 1],
                mode='markers',
                marker=dict(
                    size=8,
                    color=color,
                    line=dict(width=1, color='darkgrey')
                ),
                name=name,
                text=hover_text,
                hoverinfo='text' if hover_text is not None else 'x+y'
            )
        else:  # 3D
            trace = go.Scatter3d(
                x=X_reduced[mask, 0],
                y=X_reduced[mask, 1],
                z=X_reduced[mask, 2],
                mode='markers',
                marker=dict(
                    size=4,
                    color=color,
                    line=dict(width=0.5, color='darkgrey')
                ),
                name=name,
                text=hover_text,
                hoverinfo='text' if hover_text is not None else 'x+y+z'
            )
        
        traces.append(trace)
    
    # Add centroids if provided
    if centers is not None:
        if n_dims == 2:
            centroid_trace = go.Scatter(
                x=centers[:, 0],
                y=centers[:, 1],
                mode='markers',
                marker=dict(
                    size=12,
                    color='black',
                    symbol='star',
                    line=dict(width=1, color='white')
                ),
                name='Centroids'
            )
        else:  # 3D
            centroid_trace = go.Scatter3d(
                x=centers[:, 0],
                y=centers[:, 1],
                z=centers[:, 2],
                mode='markers',
                marker=dict(
                    size=8,
                    color='black',
                    symbol='diamond',
                    line=dict(width=1, color='white')
                ),
                name='Centroids'
            )
        
        traces.append(centroid_trace)
    
    # Create layout
    if n_dims == 2:
        layout = go.Layout(
            title=title or 'Cluster Visualization (2D)',
            hovermode='closest',
            xaxis=dict(title='Component 1'),
            yaxis=dict(title='Component 2'),
            showlegend=True,
            legend=dict(x=0, y=1)
        )
    else:  # 3D
        layout = go.Layout(
            title=title or 'Cluster Visualization (3D)',
            hovermode='closest',
            scene=dict(
                xaxis=dict(title='Component 1'),
                yaxis=dict(title='Component 2'),
                zaxis=dict(title='Component 3')
            ),
            showlegend=True,
            legend=dict(x=0, y=1)
        )
    
    fig = go.Figure(data=traces, layout=layout)
    return fig


def plot_clusters_mpl(X_reduced, labels, centers=None, title=None, figsize=(12, 8), ax=None):
    """
    Plot clusters using matplotlib.
    
    Parameters
    ----------
    X_reduced : numpy.ndarray
        Reduced data (2D or 3D)
    labels : numpy.ndarray
        Cluster labels
    centers : numpy.ndarray, optional
        Cluster centers in reduced space
    title : str, optional
        Title for the plot
    figsize : tuple, optional
        Figure size (used only if ax is None)
    ax : matplotlib.axes.Axes, optional
        Pre-existing axes for the plot
        
    Returns
    -------
    matplotlib.axes.Axes or mpl_toolkits.mplot3d.Axes3D
        The axes with the plot
    """
    n_dims = X_reduced.shape[1]
    if n_dims not in (2, 3):
        raise ValueError("Data must be reduced to 2 or 3 dimensions")
    
    unique_labels = np.unique(labels)
    n_clusters = len(unique_labels)
    colors = plt.cm.rainbow(np.linspace(0, 1, n_clusters))
    
    # Create figure and axes if not provided
    if n_dims == 2:
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)
        
        for i, label in enumerate(unique_labels):
            if label == -1:  # Noise points in DBSCAN
                color = 'gray'
                marker = 'x'
            else:
                color = colors[i]
                marker = 'o'
            
            mask = labels == label
            ax.scatter(X_reduced[mask, 0], X_reduced[mask, 1], 
                       c=[color], marker=marker, label=f'Cluster {label}')
        
        if centers is not None:
            ax.scatter(centers[:, 0], centers[:, 1], 
                       c='black', marker='*', s=200, label='Centroids')
        
        if title:
            ax.set_title(title)
        else:
            ax.set_title('Cluster Visualization (2D)')
        ax.set_xlabel('Component 1')
        ax.set_ylabel('Component 2')
        ax.legend()
        ax.grid(alpha=0.3)
        
    else:  # 3D plot
        if ax is None:
            fig = plt.figure(figsize=figsize)
            ax = fig.add_subplot(111, projection='3d')
        
        for i, label in enumerate(unique_labels):
            if label == -1:  # Noise points in DBSCAN
                color = 'gray'
                marker = 'x'
            else:
                color = colors[i]
                marker = 'o'
            
            mask = labels == label
            ax.scatter(X_reduced[mask, 0], X_reduced[mask, 1], X_reduced[mask, 2],
                      c=[color], marker=marker, label=f'Cluster {label}')
        
        if centers is not None:
            ax.scatter(centers[:, 0], centers[:, 1], centers[:, 2],
                      c='black', marker='*', s=200, label='Centroids')
        
        if title:
            ax.set_title(title)
        else:
            ax.set_title('Cluster Visualization (3D)')
        ax.set_xlabel('Component 1')
        ax.set_ylabel('Component 2')
        ax.set_zlabel('Component 3')
        ax.legend()
    
    plt.tight_layout()
    return ax


def plot_elbow_method(k_range, inertias, annotate=True, ax=None, figsize=(10, 6)):
    """
    Plot the elbow curve to visualize optimal k selection.
    
    Parameters
    ----------
    k_range : range or list
        Range of k values used
    inertias : list
        List of inertia values for each k
    annotate : bool, optional
        Whether to add annotations to the plot
    ax : matplotlib.axes.Axes, optional
        Pre-existing axes for the plot
    figsize : tuple, optional
        Figure size (used only if ax is None)
        
    Returns
    -------
    matplotlib.axes.Axes
        The axes with the plot
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    
    ax.plot(k_range, inertias, 'o-', markersize=8, markerfacecolor='blue', markeredgecolor='black')
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.set_xlabel('Number of Clusters (k)', fontsize=12)
    ax.set_ylabel('Inertia', fontsize=12)
    ax.set_title('Elbow Method for Optimal k', fontsize=14)
    ax.set_xticks(k_range)
    
    # Add annotations if requested
    if annotate:
        for i, k in enumerate(k_range):
            ax.annotate(f"{inertias[i]:.0f}", 
                       (k, inertias[i]), 
                       textcoords="offset points",
                       xytext=(0,10), 
                       ha='center')
    
    return ax


def plot_pairplot(df, hue=None, title=None, **kwargs):
    """
    Create a pairplot to visualize relationships between features.
    
    Parameters
    ----------
    df : polars.DataFrame or pandas.DataFrame
        The dataset to visualize
    hue : str, optional
        Column to use for coloring the points
    title : str, optional
        Title for the plot
    **kwargs : dict
        Additional arguments to pass to sns.pairplot
        
    Returns
    -------
    seaborn.axisgrid.PairGrid
        The seaborn PairGrid object with the pairplot
    """
    # Convert to pandas if polars DataFrame
    if not isinstance(df, pd.DataFrame):
        df = df.to_pandas()
    
    # Note: seaborn's pairplot returns a PairGrid object, not regular axes
    g = sns.pairplot(df, hue=hue, palette='viridis', **kwargs)
    
    if title:
        g.fig.suptitle(title, y=1.02)
    
    return g


def display_features_importance(model, feature_names, n_features=10, figsize=(12, 8), 
                               color_palette="viridis", threshold=None, 
                               return_data=False, ax=None):
    """
    Visualize and analyze feature importances from a tree-based model.
    
    Parameters
    ----------
    model : sklearn estimator
        A fitted tree-based model with a feature_importances_ attribute
    feature_names : list or array
        Names of the features used in the model
    n_features : int, default=10
        Number of top features to display in the plot
    figsize : tuple of int, default=(12, 8)
        Figure dimensions (used only if ax is None)
    color_palette : str or list, default="viridis"
        Color palette to use for the plot
    threshold : float, optional
        If specified, highlight features with importance above this threshold
    return_data : bool, default=False
        Whether to return the DataFrame with feature importances
    ax : matplotlib.axes.Axes, optional
        Pre-existing axes for the plot
        
    Returns
    -------
    tuple or matplotlib.axes.Axes
        If return_data=True, returns (ax, DataFrame), otherwise just ax
    """
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    # Check if the model has feature_importances_ attribute
    if not hasattr(model, 'feature_importances_'):
        raise AttributeError("Model does not have feature_importances_ attribute. "
                            "Make sure to use a tree-based model.")
    
    # Extract and sort feature importances
    importances = model.feature_importances_
    
    # Create DataFrame with all features
    full_importance_df = pd.DataFrame({
        "Feature": feature_names,
        "Importance": importances
    }).sort_values(by="Importance", ascending=False)
    
    # Select top N features
    n_features = min(n_features, len(feature_names))
    indices = np.argsort(importances)[::-1][:n_features]
    top_features = np.array(feature_names)[indices]
    top_importances = importances[indices]
    
    importance_df = pd.DataFrame({
        "Feature": top_features,
        "Importance": top_importances
    }).sort_values(by="Importance", ascending=False)
    
    # Calculate cumulative importance
    importance_df["Cumulative"] = importance_df["Importance"].cumsum()
    
    # Create plot
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    
    sns.barplot(x="Importance", y="Feature", data=importance_df, palette=color_palette, ax=ax)
    
    # Add threshold line if specified
    if threshold is not None:
        ax.axvline(x=threshold, color='red', linestyle='--', 
                   label=f'Threshold: {threshold:.3f}')
        ax.legend()
    
    # Annotate bars with importance values
    for i, v in enumerate(top_importances):
        ax.text(v + 0.01, i, f"{v:.3f}", va='center')
    
    # Add cumulative importance as text
    for i, row in importance_df.iterrows():
        ax.text(0.95, i, f"{row['Cumulative']:.2f}", va='center', 
               transform=ax.get_yaxis_transform())
    
    ax.set_title("Top Feature Importances", fontsize=16)
    ax.set_xlabel("Importance", fontsize=14)
    ax.set_ylabel("Feature", fontsize=14)
    ax.grid(axis="x", linestyle="--", alpha=0.6)
    
    # Print additional insights
    print(f"Top {n_features} features account for {importance_df['Importance'].sum():.2%} of total importance")
    
    if return_data:
        return ax, full_importance_df
    return ax