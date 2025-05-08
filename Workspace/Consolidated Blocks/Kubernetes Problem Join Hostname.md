
**Kubernetes Unique Hostname Join Problem**

The provisioning workflow for Kubernetes clusters involves distinct phases: build time and provision time. During build time, the operating system, network, and DNS configurations are established, and certificates for Kubernetes components are generated. Both master and worker node images are configured with these settings. At provision time, the master node is deployed first, generating a secret used for secure communication within the cluster. Worker nodes are subsequently provisioned, joining the cluster using this secret to authenticate their membership. However, a critical issue arises with the static VM images used for worker nodes. These images, created during the build phase, have a fixed hostname embedded within them, such as 'k8s-worker'. When multiple worker nodes are provisioned from the same static image, they inherit this identical hostname, leading to conflicts within Kubernetes. Kubernetes mandates unique hostnames for each node to ensure proper identification and management. Consequently, while the first worker node with a given hostname can successfully join the cluster, additional nodes with the same hostname are rejected, preventing them from joining. This limitation severely impacts scalability and operational functionality, as Kubernetes cannot differentiate between nodes with identical hostnames. To resolve this issue, a dynamic mechanism for hostname configuration is required, enabling each worker node to receive a unique identifier at provision time without relying on static image settings. This adjustment would allow all nodes to join the Kubernetes cluster successfully, enhancing scalability and ensuring robust cluster operations.

---

```latex
\subsection{Nix K8S Hostname Problem}

While provisioning Kubernetes worker nodes on NixOS using a flake-based configuration and remote automation via Python over SSH, we encountered a reproducible but non-deterministic failure during the execution of the following command:

\begin{verbatim}
sudo nixos-rebuild switch --flake /etc/nixos/current-systemconfig#k8s-worker
\end{verbatim}

This command intermittently fails with a non-zero exit code during the \texttt{building the system configuration} step when executed as part of an automated script. Surprisingly, some configuration changes---notably the hostname update---appear to take effect, despite the failure. When the exact same command is re-executed manually via SSH, it completes successfully, applying the full configuration and starting all required services.

A deeper analysis revealed the underlying cause is linked to the startup sequence of the Kubernetes services on the worker node, in particular the interaction between \texttt{certmgr}, the hostname change, and the bootstrap token mechanism:

\begin{itemize}
    \item The node's hostname is updated as part of the NixOS rebuild.
    \item Simultaneously, Kubernetes-related services such as \texttt{certmgr}, \texttt{kubelet}, and \texttt{flannel} are started.
    \item \texttt{certmgr} immediately attempts to request TLS certificates from the Kubernetes master node, using a bootstrap token for authentication.
    \item This request fails with errors such as \texttt{invalid token} or \texttt{authentication error. Giving up without retries}, as the master node does not recognize the node (due to the just-updated hostname) or the token is not yet registered.
    \item Because certificate retrieval fails, dependent services such as \texttt{kubelet} and \texttt{flannel} cannot start properly, causing the rebuild to report a failure.
\end{itemize}

The correct provisioning strategy involves splitting the process into discrete steps:

\begin{enumerate}
    \item Apply the initial NixOS configuration to set the hostname, but without enabling Kubernetes services.
    \item Manually generate and register a valid bootstrap token on the Kubernetes master node.
    \item Inject this token into the worker node's configuration and then re-apply the full configuration with Kubernetes services enabled.
\end{enumerate}

This sequence ensures that the hostname is recognized by the master node and that the certificate request from \texttt{certmgr} can be authenticated successfully. Notably, private keys used in the certificate process are generated locally and are never transmitted, ensuring secure provisioning. This failure mode highlights the sensitivity of NixOS declarative infrastructure to ordering and timing during initial cluster bootstrap.
```

Would you like a French version as well?