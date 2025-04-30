{ config, pkgs, lib, ... }:

{
  # Configuration de base
  boot.kernelPackages = pkgs.linuxPackages_6_1;
  boot.loader.systemd-boot.enable = true;
  boot.loader.efi.canTouchEfiVariables = true;

  networking.useNetworkd = true;
  systemd.network.enable = true;
  services.avahi = {
    enable = true;
    nssmdns4 = true;
    publish = {
      enable = true;
      addresses = true;
      domain = true;
      workstation = true;
    };
  };

  nix.settings.experimental-features = [ "nix-command" "flakes" ];
  time.timeZone = "UTC";

  users.users.odancona = {
    isNormalUser = true;
    initialHashedPassword = "$y$j9T$u8873E9Qlnqv13YKSP2NB/$pgKfnnIDxsnoUVr9uXXYRqAdajpKDn5la2UShIw36z.";
    extraGroups = [ "wheel" ];
    openssh.authorizedKeys.keys = [
      (builtins.readFile /home/olivier/.ssh/rhodey.pub)
      (builtins.readFile /home/olivier/.ssh/id_ed25519.pub)
    ];
  };

  services.openssh.enable = true;

  environment.systemPackages = with pkgs; [
    vim curl tree btop bat fastfetch git jq
  ];

  swapDevices = [];
  virtualisation.diskSize = 16384; # 16GB

  system.stateVersion = "24.05";
}