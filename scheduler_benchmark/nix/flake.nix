{
  description = "NixOS Kubernetes VM";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/24.11";
    nixos-generators = {
      url = "github:nix-community/nixos-generators";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, nixos-generators }: {
    packages.x86_64-linux = {
      qcow = nixos-generators.nixosGenerate {
        system = "x86_64-linux";
        modules = [
          ./vm-config.nix
        ];
        format = "qcow";
      };
    };
  };
}