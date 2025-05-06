Très bonne question — tu touches à un **point fondamental de l’écosystème NixOS** : comment garder la **souplesse de `nixos-rebuild switch`** dans une image générée de manière déclarative (genre `nixos-generators`), **sans reconstruire une image pour chaque hôte**.

---

## 🧠 TL;DR : Ce que tu veux faire

Tu veux :

1. Générer **une seule image VM (qcow2)** avec `nixos-generators` ou `nixos-rebuild build-vm`.
2. Déployer cette image sur plusieurs machines (ou pods Kubernetes).
3. Et depuis **l’intérieur de chaque VM**, pouvoir faire un :

   ```bash
   sudo nixos-rebuild switch --flake /etc/nixos
   ```

   pour adapter la conf locale (ex: hostname), **sans conflit de fileSystems**.

---

## 🔥 Le vrai problème

Tu l’as bien compris :

* `nixos-generators` **injecte son propre `fileSystems."/".device`** (ex: `/dev/disk/by-label/nixos`).
* Et ton `configuration.nix` (ou flake) injecte **un autre chemin** (genre `/dev/vda3`).
* Lors d’un `nixos-rebuild`, **ces deux définitions entrent en conflit**, d’où l’erreur :

  ```
  conflicting definition values for fileSystems."/".device
  ```

---

## ✅ Solution canonique : utiliser `lib.mkDefault` ou `lib.mkForce`

Il y a **2 solutions idiomatiques** selon ton cas :

### 1. **lib.mkDefault** : ton config prend le dessus **s'il est défini**

Utilise `lib.mkDefault` dans le fichier utilisé par `nixos-generators` :

```nix
{
  fileSystems."/" = {
    device = lib.mkDefault "/dev/disk/by-label/nixos";
    fsType = "ext4";
  };
}
```

Et dans ton flake perso (par exemple `/etc/nixos/flake.nix` dans la VM), tu mets :

```nix
{
  fileSystems."/" = {
    device = "/dev/vda3";  # par exemple
    fsType = "ext4";
  };
}
```

➡️ Résultat : quand tu fais `nixos-rebuild switch`, **le device `/dev/vda3` sera utilisé**, car il "override" le `mkDefault`.

---

### 2. **lib.mkForce** : tu forces la valeur **depuis l’intérieur de la VM**

Si tu veux vraiment **écraser quoi qu’il arrive**, tu peux aussi faire :

```nix
fileSystems."/" = lib.mkForce {
  device = "/dev/vda3";
  fsType = "ext4";
};
```

Mais c’est à réserver si tu **sais exactement ce que tu fais**, car ça empêche toute autre config de s'exprimer.

---

## 🧰 Astuce pratique : inclure la config flake dans l’image

Dans ton `configuration.nix` de l’image :

```nix
{
  # Inclure la config dans l'image
  environment.etc."nixos".source = ./.;
}
```

➡️ Résultat : après boot, tu as `/etc/nixos/flake.nix` présent dans la VM, donc `nixos-rebuild` fonctionne.

---

## 🧬 Cas Kubernetes : hostname dynamique

Si tu veux **changer dynamiquement le hostname sans reconstruire**, tu peux utiliser une **option configurable par un fichier externe ou une variable d’env**.

Exemple :

```nix
{
  networking.hostName = builtins.getEnv "HOSTNAME";
}
```

Ou depuis un fichier lu dynamiquement (via `lib.mkIf (builtins.pathExists ...)`), ou mieux via **flakes inputs** + `nixosConfigurations."${hostname}"`.

---

## ✅ Résumé canonique

| Problème                                 | Solution                                                                                  |
| ---------------------------------------- | ----------------------------------------------------------------------------------------- |
| `fileSystems` en conflit                 | Utiliser `lib.mkDefault` dans l'image, et une valeur définie dans la config personnalisée |
| Rebuild depuis la VM sans repo git       | Copier le flake dans `/etc/nixos` à la génération                                         |
| `nixos-rebuild` échoue car pas de config | Ajouter le flake ou config.nix dans `/etc/nixos` via `environment.etc`                    |
| Configuration dynamique (hostname, etc.) | Utiliser `builtins.getEnv`, ou passer des valeurs via cloud-init/env                      |

---

Souhaites-tu un exemple complet de flake qui fait ça proprement ?
