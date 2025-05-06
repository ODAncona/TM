{ config, pkgs, lib, self, ... }:

let
  username = "odancona";
  password = "$y$j9T$u8873E9Qlnqv13YKSP2NB/$pgKfnnIDxsnoUVr9uXXYRqAdajpKDn5la2UShIw36z.";
  rhodeyPublicKey = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCt/BcJGPSnv1s7yY73D5sOSqnKXkWVyBMhypJthm1HVzVZc2Yn0B8J+iWnxUbsR6ysy8W2/f1h3tLRlB2+ZejeSmYV5hqVsnit+eD6oCQtLegOerd6wY1igVF0tp8YOQDfTnRQkSmrpCBTZuvVu1HMvfmGK4Po6K1rkjRcGGGmWz7azlSEr3tjfWoEmgSO3Zutx8b/Y8Qi4Th5TLBjb6S5EqMGPfM9zWrDgCCOez4PzWRnmnO9fZX3QeSJFFw/Tmnh9lSPuPnZg+FYVsKx6Ob16heJgwq4fv3tig9LQAWMGr+5q55ylv3Zq7THXCdWH8na6rKg4ns9+wWY1xvK++uSC6Of9dOzsyX+hafRhxzgOdGcrk8W0h5N9L5T+Be+4RIs79w2NKe5Iqfagx+TvqHHQp2u1XbkT1do2GOba+l5GWuG+ar1mtddjZvy3jz1hfh+wN7+U6bV9rc81nAnoLS1kA0mEFy+D9YDg0+9cOTpfi60gxZjPrVhRY3h5Ufswhfhyu6MMk1MBZw9GZ9BxvXfGCGup+4yP36+7joOAYshp0WYPVQA+mnX06gYmIukITB0D5/1+YtU2K9qLxkAzmyi/RkZ0ryqmy1n+CViTxbP2yFdGjpixe+Dsi2COYCV0YXw1bTKpzjUKSkdHh6VYgUFaJGvJvet4mXwoAlsejBtWw== rhodey access";
  x1CarbonPublicKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFLVwuRVt0pNYdSptuvtKQqIg7Rd6Thkx/q7BkMCcppl olivier.dancona@heig-vd.ch";
in
{
  # ~~~ System Configuration ~~~
  boot.kernelPackages = pkgs.linuxPackages_6_1;
  boot.loader.systemd-boot.enable = true;
  boot.loader.efi.canTouchEfiVariables = true;
  services.openssh.enable = true;
  swapDevices = [];
  system.stateVersion = "24.05";
  virtualisation.diskSize = 16384; # 16GB
  environment.systemPackages = with pkgs; [
    vim curl tree btop bat fastfetch git jq openssl
  ];
  nix.settings.experimental-features = [ "nix-command" "flakes" ];
  fileSystems."/" = lib.mkForce {
    device = "/dev/vda3";
    fsType = "ext4";
  };

  # ~~~ Networking Configuration ~~~
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

  # ~~~ User Configuration ~~~
  time.timeZone = "UTC";
  users.users.${username} = {
    isNormalUser = true;
    initialHashedPassword = password;
    extraGroups = [ "wheel" ];
    openssh.authorizedKeys.keys = [ rhodeyPublicKey x1CarbonPublicKey ];
  };
  security.sudo.wheelNeedsPassword = false;

  # ~~~ Flake Copy ~~~
  system.activationScripts.saveFlakeConfig = {
    deps = [];
    text = ''
      rm -rf /etc/nixos/current-systemconfig
      mkdir -p /etc/nixos/current-systemconfig
      cp -rf ${self}/* /etc/nixos/current-systemconfig/
      cd /etc/nixos/current-systemconfig
      chown -R ${username}:users /etc/nixos/current-systemconfig
      chmod -R u=rwX,g=rX,o=rX /etc/nixos/current-systemconfig
    '';
  };

}