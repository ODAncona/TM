🧠 Why the previous image failed:
When you used nixos-generate -f qcow before with a config that didn't specify a bootloader, you got a "blank" root filesystem. But now — with your posted config — the generated .qcow2 image is absolutely ready for:

```bash
virt-install --name nixos-test --memory 4096 --vcpus 2 \
  --disk path=/home/odancona/.local/share/libvirt/images/nixos.img,format=qcow2 \
  --os-variant generic --import \
  --network network=scheduler_benchmark_net --noautoconsole
```
✅ It should boot and work!
If it still hangs, I’d check:

Make sure you are using UEFI boot if the VM is expecting EFI (since systemd-boot is used) — or:

Adjust your config to use GRUB for BIOS mode.