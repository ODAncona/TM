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

      # ~~~ Kubernetes ~~~
      k8s-master = nixos-generators.nixosGenerate {
        system = "x86_64-linux";
        modules = [
          ./vm-config.nix
          ./modules/kubernetes/master.nix
        ];
        format = "qcow";
        specialArgs = { self = self; };

      };
      
      k8s-worker = nixos-generators.nixosGenerate {
        system = "x86_64-linux";
        modules = [
          ./vm-config.nix
          ./modules/kubernetes/worker.nix
        ];
        format = "qcow";
        specialArgs = { self = self; };

      };
      
      # ~~~ SLURM ~~~
      # slurm-master = nixos-generators.nixosGenerate {
      #   system = "x86_64-linux";
      #   modules = [
      #     ./vm-config.nix
      #     ./modules/slurm/master.nix
      #   ];
      #   format = "qcow";
      #   specialArgs = { self = self; };

      # };
      
      # slurm-worker = nixos-generators.nixosGenerate {
      #   system = "x86_64-linux";
      #   modules = [
      #     ./vm-config.nix
      #     ./modules/slurm/worker.nix
      #   ];
      #   format = "qcow";
      #   specialArgs = { self = self; };

      # };      
    };
  };
}