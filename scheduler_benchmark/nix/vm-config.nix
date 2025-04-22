{ config, pkgs, lib, ... }:

let
  diskSize = 16384; # 16GB in MiB

  baseSystem = { ... }: {
    boot.kernelPackages = pkgs.linuxPackages_6_1;
    boot.loader.systemd-boot.enable = true;
    boot.loader.efi.canTouchEfiVariables = true;

    networking.useDHCP = true;
    networking.useNetworkd = true;
    systemd.network.enable = true;

    nix.settings.experimental-features = [ "nix-command" "flakes" ];
    time.timeZone = "UTC";

    users.users.odancona = {
      isNormalUser = true;
      initialPassword = "password";
      extraGroups = [ "wheel" ];
      openssh.authorizedKeys.keys = [
        (builtins.readFile /home/olivier/.ssh/rhodey.pub)
        (builtins.readFile /home/olivier/.ssh/id_ed25519.pub)
      ];
    };

    services.openssh.enable = true;

    environment.systemPackages = with pkgs; [
      vim
      curl
      tree
      btop
      bat
      fastfetch
    ];

    swapDevices = [];
    virtualisation.diskSize = diskSize;
  };

    masterConfig = import ./modules/kubernetes/master.nix { 
    inherit config lib pkgs;
  };

in
{
  imports = [
    (baseSystem { })
    # Uncomment below according to node role
    # masterConfig
  ];

  system.stateVersion = "24.05";
}