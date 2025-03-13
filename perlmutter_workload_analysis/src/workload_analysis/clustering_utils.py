"""
Utility functions for clustering analysis.

This module provides implementations of various clustering algorithms,
methods for parameter optimization, and cluster evaluation metrics.
"""

import numpy as np
import polars as pl
import pandas as pd
from tqdm.auto import tqdm
import time
from sklearn.cluster import KMeans, DBSCAN, AffinityPropagation, MeanShift
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
from sklearn.model_selection import ParameterGrid


def find_optimal_k(X, k_range=range(1, 11), random_state=42, n_init=10, max_iter=300, verbose=True):
    """
    Find the optimal number of clusters using the elbow method.
    
    Parameters
    ----------
    X : numpy.ndarray
        Input data for clustering
    k_range : range or list, optional
        Range of k values to test
    random_state : int, optional
        Random seed for kmeans
    n_init : int, optional
        Number of initializations for kmeans
    max_iter : int, optional
        Maximum number of iterations for kmeans
    verbose : bool, optional
        Whether to print progress information
        
    Returns
    -------
    tuple
        (inertias, times) where inertias is a list of inertia values for each k
        and times is a list of execution times
    """
    inertias = []
    times = []
    
    # Use tqdm to display progress bar if verbose is True
    iterator = tqdm(k_range, desc="Finding optimal k") if verbose else k_range
    
    for k in iterator:
        # Measure time for performance comparison
        start_time = time.time()
        
        # Create and fit KMeans model
        kmeans = KMeans(n_clusters=k, random_state=random_state, n_init=n_init, max_iter=max_iter)
        kmeans.fit(X)
        
        # Store inertia (sum of squared distances to closest centroid)
        inertias.append(kmeans.inertia_)
        
        elapsed_time = time.time() - start_time
        times.append(elapsed_time)
        
        if verbose:
            print(f"K={k}: Inertia={kmeans.inertia_:.2f}, Time={elapsed_time:.4f}s")
    
    return inertias, times


def search_parameters(data, labels, clustering_fct, params, scoring="silhouette_score"):
    """
    Search for best parameters for a clustering algorithm.
    
    Parameters
    ----------
    data : numpy.ndarray
        Input data for clustering
    labels : numpy.ndarray
        True labels (if using supervised metrics, None otherwise)
    clustering_fct : callable
        Clustering algorithm class (e.g., KMeans, DBSCAN)
    params : dict
        Dictionary of parameters to search
    scoring : str or callable, optional
        Scoring method ("silhouette_score" or a custom function)
        
    Returns
    -------
    tuple
        (best_params, best_score) where best_params is a dict of optimal parameters
        and best_score is the corresponding score
    """
    best_score = -float('inf')
    best_params = None
    
    for params_set in tqdm(ParameterGrid(params), desc=f"Searching parameters for {clustering_fct.__name__}"):
        estimator = clustering_fct(**params_set)
        estimator.fit(data)
        
        # Skip if we have only one cluster and using silhouette score
        if scoring == "silhouette_score" and len(np.unique(estimator.labels_)) < 2:
            continue
        
        if scoring == "silhouette_score":
            score = silhouette_score(data, estimator.labels_)
        else:
            # Assume scoring is a callable function
            score = scoring(labels, estimator.labels_)
            
        if score > best_score:
            best_score = score
            best_params = params_set
    
    return best_params, best_score


def apply_clustering(X, algorithm="kmeans", params=None):
    """
    Apply a clustering algorithm to the data.
    
    Parameters
    ----------
    X : numpy.ndarray
        Input data for clustering
    algorithm : str, optional
        Clustering algorithm to use ("kmeans", "dbscan", "affinity_propagation", "meanshift")
    params : dict, optional
        Parameters for the clustering algorithm
        
    Returns
    -------
    tuple
        (labels, centers, n_clusters) where labels are the cluster assignments,
        centers are the cluster centroids, and n_clusters is the number of clusters
    """
    if params is None:
        params = {}
    
    # Select and apply algorithm
    if algorithm.lower() == "kmeans":
        # Default parameters for KMeans
        default_params = {"n_clusters": 3, "random_state": 42, "n_init": 10}
        default_params.update(params)
        
        estimator = KMeans(**default_params)
        estimator.fit(X)
        labels = estimator.labels_
        centers = estimator.cluster_centers_
        n_clusters = len(np.unique(labels))
        
    elif algorithm.lower() == "dbscan":
        # Default parameters for DBSCAN
        default_params = {"eps": 0.5, "min_samples": 5}
        default_params.update(params)
        
        estimator = DBSCAN(**default_params)
        estimator.fit(X)
        labels = estimator.labels_
        
        # DBSCAN doesn't provide centers, so we compute them
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        centers = np.array([X[labels == i].mean(axis=0) for i in range(n_clusters)])
        
    elif algorithm.lower() == "affinity_propagation":
        # Default parameters for AffinityPropagation
        default_params = {"damping": 0.5, "random_state": 42}
        default_params.update(params)
        
        estimator = AffinityPropagation(**default_params)
        estimator.fit(X)
        labels = estimator.labels_
        centers = estimator.cluster_centers_
        n_clusters = len(np.unique(labels))
        
    elif algorithm.lower() == "meanshift":
        # Default parameters for MeanShift
        default_params = {}
        default_params.update(params)
        
        estimator = MeanShift(**default_params)
        estimator.fit(X)
        labels = estimator.labels_
        centers = estimator.cluster_centers_
        n_clusters = len(np.unique(labels))
    
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    
    return labels, centers, n_clusters