kubernetes on nix
https://joshrosso.com/c/nix-k8s/
https://nixos.wiki/wiki/Kubernetes
https://www.youtube.com/watch?v=SEA1Qm8K4gY
https://nlewo.github.io/nixos-manual-sphinx/configuration/kubernetes.xml.html


https://discourse.nixos.org/t/kubernetes-on-nix-community-organization/20457
https://github.com/hall/kubenix
https://github.com/DBCDK/kubernixos
https://github.com/justinas/nixos-ha-kubernetes


script install k8s
https://github.com/techiescamp/vagrant-kubeadm-kubernetes/tree/main/scripts


commands:

vérifier les SANs du certificat:
`openssl x509 -in /var/lib/kubernetes/secrets/kube-apiserver.pem -noout -text | grep DNS`

vérifier que le API server soit dispo depuis le worker:
nc -vz k8s-master.local 6443

sylvan dmarc_rua@infinisil.com contact@infinisil.com nca@infinisil.com

port ouvert:
sudo ss -ltnp | grep 6443

secrets bien générés?
sudo ls -lh /var/lib/kubernetes/secrets/

check le contenu du certificat
nix-shell -p openssl --run 'openssl x509 -in /var/lib/kubernetes/secrets/kube-apiserver.pem -noout -text | grep DNS'


echo 43d41da727f71fb7a745dd08852b8caf | sudo nixos-kubernetes-node-join
43d41da727f71fb7a745dd08852b8caf