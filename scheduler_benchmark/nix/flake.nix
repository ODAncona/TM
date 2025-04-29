# {
#   description = "NixOS Kubernetes VM";

#   inputs = {
#     nixpkgs.url = "github:NixOS/nixpkgs/24.11";
#     nixos-generators = {
#       url = "github:nix-community/nixos-generators";
#       inputs.nixpkgs.follows = "nixpkgs";
#     };
#   };

#   outputs = { self, nixpkgs, nixos-generators }: {
#     packages.x86_64-linux = {
#       qcow = nixos-generators.nixosGenerate {
#         system = "x86_64-linux";
#         modules = [
#           ./vm-config.nix
#         ];
#         format = "qcow";
#       };
#     };
#   };
# }

{
  description = "NixOS Cluster VMs";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/24.11";
    nixos-generators = {
      url = "github:nix-community/nixos-generators";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, nixos-generators }: {
    packages.x86_64-linux = {
      # Images Kubernetes
      k8s-master = nixos-generators.nixosGenerate {
        system = "x86_64-linux";
        modules = [
          ./vm-config.nix
          ./modules/kubernetes/master.nix
        ];
        format = "qcow";
      };
      
      k8s-worker = nixos-generators.nixosGenerate {
        system = "x86_64-linux";
        modules = [
          ./vm-config.nix
          ./modules/kubernetes/worker.nix
        ];
        format = "qcow";
      };
      
      # Images Slurm
      # slurm-master = nixos-generators.nixosGenerate {
      #   system = "x86_64-linux";
      #   modules = [
      #     ./vm-config.nix
      #     ./modules/slurm/master.nix
      #   ];
      #   format = "qcow";
      # };
      
      # slurm-worker = nixos-generators.nixosGenerate {
      #   system = "x86_64-linux";
      #   modules = [
      #     ./vm-config.nix
      #     ./modules/slurm/worker.nix
      #   ];
      #   format = "qcow";
      # };
      
      # Alias pour compatibilité
      qcow = self.packages.x86_64-linux.k8s-master;
    };
  };
}