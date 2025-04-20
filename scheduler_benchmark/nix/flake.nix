{
  description = "NixOS Kubernetes VM";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-23.11";
  };

  outputs = { self, nixpkgs }: {
    nixosConfigurations = {
      kubernetesMaster = nixpkgs.lib.nixosSystem {
        system = "x86_64-linux";
        modules = [ ./vm-config.nix ];
      };
    };
  };
}