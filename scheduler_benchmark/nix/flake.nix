{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    nixos-generators = {
      url = "github:nix-community/nixos-generators";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, nixos-generators }: let
    system = "x86_64-linux";
    vmModules = [
      ({ config, pkgs, lib, ... }: {
        system.stateVersion = "24.11";
        boot.kernelPackages = pkgs.linuxPackages_6_1;
        boot.loader.systemd-boot.enable = true;
        boot.loader.efi.canTouchEfiVariables = true;
        networking.hostName = "rhodey-vm";
        networking.interfaces.eth0.useDHCP = true;
        time.timeZone = "UTC";
        users.users.odancona = {
        isNormalUser = true;
        initialPassword = "password";
        extraGroups = [ "wheel" ];
        openssh.authorizedKeys.keys = [ (builtins.readFile /home/olivier/.ssh/rhodey.pub) (builtins.readFile /home/olivier/.ssh/id_ed25519.pub) ];
        };
        services.openssh.enable = true;
        environment.systemPackages = with pkgs; [ vim curl tree ];
        virtualisation.diskSize = lib.mkForce 16384; # 16GB in MiB
      })
    ];
  in {
    nixosConfigurations.rhodey-vm = nixpkgs.lib.nixosSystem {
      inherit system;
      modules = vmModules;
    };
    packages.${system}.qcow2 = nixos-generators.nixosGenerate {
      inherit system;
      modules = vmModules;
      format = "qcow2";
    };
  };
}