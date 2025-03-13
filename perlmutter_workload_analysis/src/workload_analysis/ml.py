def evaluate_random_forest(model, X_test, y_test, class_names=None, display_results=True):
    """
    Evaluate a Random Forest classifier with multiple performance metrics.
    
    This function calculates and optionally displays key classification metrics
    including accuracy, precision, recall, F1-score, ROC AUC, confusion matrix,
    and a detailed classification report.
    
    Parameters
    ----------
    model : sklearn estimator
        A fitted Random Forest or similar model with predict and predict_proba methods
    X_test : array-like of shape (n_samples, n_features)
        Test features to evaluate the model on
    y_test : array-like of shape (n_samples,)
        True labels for the test data
    class_names : list of str, optional
        Custom names for the classes (e.g., ["Negative", "Positive"])
        If None, defaults to ["False", "True"] for binary classification
    display_results : bool, default=True
        Whether to print the classification report and display the confusion matrix
        
    Returns
    -------
    dict
        Dictionary containing evaluation metrics:
        - accuracy: Overall prediction accuracy
        - precision: Precision score (tp / (tp + fp))
        - recall: Recall score (tp / (tp + fn))
        - f1_score: F1 score (harmonic mean of precision and recall)
        - roc_auc: Area under the ROC curve
        - confusion_matrix: The confusion matrix as a numpy array
    
    Examples
    --------
    >>> from sklearn.ensemble import RandomForestClassifier
    >>> from sklearn.model_selection import train_test_split
    >>> X_train, X_test, y_train, y_test = train_test_split(X, y)
    >>> model = RandomForestClassifier().fit(X_train, y_train)
    >>> metrics = evaluate_random_forest(model, X_test, y_test)
    >>> print(f"Model accuracy: {metrics['accuracy']:.2f}")
    """
    from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                               f1_score, roc_auc_score, classification_report,
                               confusion_matrix, roc_curve, auc)
    import matplotlib.pyplot as plt
    import numpy as np
    import seaborn as sns
    
    # Get predictions and probabilities
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]  
    
    # Convert to integer type if necessary for metrics calculation
    y_test_int = y_test.astype(int)
    y_pred_int = y_pred.astype(int)
    
    # Calculate metrics
    cm = confusion_matrix(y_test_int, y_pred_int)
    
    metrics = {
        "accuracy": accuracy_score(y_test_int, y_pred_int),
        "precision": precision_score(y_test_int, y_pred_int),
        "recall": recall_score(y_test_int, y_pred_int),
        "f1_score": f1_score(y_test_int, y_pred_int),
        "roc_auc": roc_auc_score(y_test_int, y_proba),
        "confusion_matrix": cm
    }
    
    if display_results:
        # Set default class names if not provided
        if class_names is None:
            class_names = ["False", "True"]
            
        # Print classification report
        print("Classification Report:")
        print(classification_report(y_test_int, y_pred_int, target_names=class_names))
        
        # Display confusion matrix
        print("\nConfusion Matrix:")
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                    xticklabels=class_names, yticklabels=class_names)
        plt.xlabel('Predicted')
        plt.ylabel('True')
        plt.title('Confusion Matrix')
        plt.tight_layout()
        plt.show()
        
        # Plot ROC curve
        fpr, tpr, _ = roc_curve(y_test_int, y_proba)
        roc_auc = auc(fpr, tpr)
        
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, color='darkorange', lw=2, 
                 label=f'ROC curve (area = {roc_auc:.2f})')
        plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Receiver Operating Characteristic')
        plt.legend(loc="lower right")
        plt.grid(alpha=0.3)
        plt.show()
    
    return metrics

