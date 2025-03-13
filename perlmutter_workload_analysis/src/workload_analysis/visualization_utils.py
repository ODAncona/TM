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


def plot_clusters_mpl(X_reduced, labels, centers=None, title=None, figsize=(12, 8)):
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
        Figure size
        
    Returns
    -------
    matplotlib.pyplot.Figure
        The generated plot
    """
    n_dims = X_reduced.shape[1]
    if n_dims not in (2, 3):
        raise ValueError("Data must be reduced to 2 or 3 dimensions")
    
    unique_labels = np.unique(labels)
    n_clusters = len(unique_labels)
    colors = plt.cm.rainbow(np.linspace(0, 1, n_clusters))
    
    if n_dims == 2:
        plt.figure(figsize=figsize)
        
        for i, label in enumerate(unique_labels):
            if label == -1:  # Noise points in DBSCAN
                color = 'gray'
                marker = 'x'
            else:
                color = colors[i]
                marker = 'o'
            
            mask = labels == label
            plt.scatter(X_reduced[mask, 0], X_reduced[mask, 1], 
                       c=[color], marker=marker, label=f'Cluster {label}')
        
        if centers is not None:
            plt.scatter(centers[:, 0], centers[:, 1], 
                       c='black', marker='*', s=200, label='Centroids')
        
        plt.title(title or 'Cluster Visualization (2D)')
        plt.xlabel('Component 1')
        plt.ylabel('Component 2')
        plt.legend()
        plt.grid(alpha=0.3)
        
    else:  # 3D plot
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
        
        ax.set_title(title or 'Cluster Visualization (3D)')
        ax.set_xlabel('Component 1')
        ax.set_ylabel('Component 2')
        ax.set_zlabel('Component 3')
        ax.legend()
    
    plt.tight_layout()
    return plt.gcf()

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


def plot_elbow_method(k_range, inertias, annotate=True):
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
        
    Returns
    -------
    matplotlib.pyplot.Figure
        The generated elbow plot
    """
    plt.figure(figsize=(10, 6))
    plt.plot(k_range, inertias, 'o-', markersize=8, markerfacecolor='blue', markeredgecolor='black')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xlabel('Number of Clusters (k)', fontsize=12)
    plt.ylabel('Inertia', fontsize=12)
    plt.title('Elbow Method for Optimal k', fontsize=14)
    plt.xticks(k_range)
    
    # Add annotations if requested
    if annotate:
        for i, k in enumerate(k_range):
            plt.annotate(f"{inertias[i]:.0f}", 
                         (k, inertias[i]), 
                         textcoords="offset points",
                         xytext=(0,10), 
                         ha='center')
    
    return plt.gcf()

def plot_pairplot(df, hue=None, title=None):
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
        
    Returns
    -------
    matplotlib.pyplot.Figure
        The generated pairplot figure
    """
    # Convert to pandas if polars DataFrame
    if not isinstance(df, pd.DataFrame):
        df = df.to_pandas()
    
    plt.figure(figsize=(15, 10));
    g = sns.pairplot(df, hue=hue, palette='viridis')
    
    if title:
        g.fig.suptitle(title, y=1.02)
    
    return g