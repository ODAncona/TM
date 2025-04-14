{ config, pkgs, lib, ... }: {
    # Boot loader
    boot.kernelPackages = pkgs.linuxPackages_6_1;
    boot.loader.systemd-boot.enable = true;
    boot.loader.efi.canTouchEfiVariables = true;

    # Networking
    networking.hostName = "nix-vm";
    networking.useDHCP = true;
    networking.useNetworkd = true;
    systemd.network.enable = true;


    # System Configuration
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
    virtualisation.diskSize = lib.mkForce 16384; # 16GB in MiB
    system.stateVersion = "24.11";
}