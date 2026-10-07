# dmesg Anomaly Fixes — Gigabyte B450M S2H / Ubuntu 7.0.0-34

## Tier 0 — Hardware/Firmware/IOMMU (Critical)

### 1. NVMe IOMMU IO_PAGE_FAULT (line 1008)

```bash
# Check IOMMU status
dmesg | grep -i "AMD-Vi\|iommu\|IO_PAGE_FAULT"
# Disable IOMMU temporarily to test if NVMe works
# Add to kernel cmdline in /etc/default/grub:
#   GRUB_CMDLINE_LINUX="... irqpoll acpi_irq_balance acpi_force_table_verification iommu=pt"
# or: noiommu (completely disable IOMMU)
sudo update-grub && sudo reboot
# Verify IOMMU fault is gone
dmesg | grep -i "IO_PAGE_FAULT"
# Check IOMMU groups
ls /sys/kernel/iommu_groups/
```

### 2. SWIOTLB Fallback / IOMMU DMA (line 693)

```bash
# Ensure IOMMU is enabled in BIOS/UEFI
# Check current IOMMU status
dmesg | grep "AMD-Vi" | head -20
# Update firmware
sudo apt install amd64-microcode linux-firmware
# If IOMMU still not working, force SWIOTLB explicitly:
# GRUB_CMDLINE_LINUX="... iommu=pt swiotlb=1"
sudo update-grub
```

### 3. NVMe Unchecked Data Buffer (line 1312)

```bash
# Check NVMe health and firmware
sudo nvme smart-log /dev/nvme0
sudo nvme id-ctrl /dev/nvme0
sudo nvme verify /dev/nvme0n1
# Force checked buffers
# Kernel param: nvme_core.use_cmb_sqes=0
sudo update-initramfs -u -k all
```

### 4. Broken BIOS / AMD Secure Processor CCP (line 1140)

```bash
# Check current BIOS version
sudo dmidecode -s bios-version
# Download latest BIOS from Gigabyte:
# https://www.gigabyte.com/Motherboards/B450M-S2H-rev-1x#support
# Update via BIOS flash utility (Q-Flash Plus) using USB drive
# Or use fwupdate in Ubuntu:
sudo apt install fwupdate
# After BIOS update, verify CCP:
dmesg | grep "ccp" | tail -10
```

### 5. ACPI Resource Conflict (lines 1145-1146)

```bash
# Add kernel parameter to handle ACPI resource conflicts
sudo nano /etc/default/grub
# Add to GRUB_CMDLINE_LINUX:
#   acpi_osi=Linux acpi_enforce_resources=lax
sudo update-grub
# Verify SMBus driver loads correctly
sudo modprobe i2c-dev
sudo i2cdetect -l
lspci | grep -i smb
```

### 6. ACPI Thermal Zone Failures (lines 725, 728)

```bash
# Check thermal zones
cat /sys/class/thermal/thermal_zone*/temp
# Use generic thermald config
sudo cp /usr/share/thermald/thermal-conf.xml /etc/thermald/thermal-conf.xml
sudo systemctl enable --now thermald
# Check CPU temperature
sensors
```

### 7. USB 1-4 Enumeration Failure (lines 947-1022)

```bash
# Identify the failing USB device
lsusb -t
lsusb | grep -i "1-4"
# Power cycle the USB port
echo 0 | sudo tee /sys/bus/usb/devices/1-4/authorized
echo 1 | sudo tee /sys/bus/usb/devices/1-4/authorized
# If persistent, disable the port
echo 0 | sudo tee /sys/bus/usb/devices/1-4/authorized
# Update xHCI firmware
sudo apt install linux-firmware
# If all USB 1-4 devices fail, the port/hub is physically damaged
```

### 8. SATA Link Drops (lines 951-953, 986)

```bash
# Check SATA port status and health
sudo smartctl -i /dev/sda
sudo smartctl -i /dev/sdb
sudo smartctl -i /dev/sdc
# Check link speed
dmesg | grep "SATA link"
# Force link speed if unstable
# Check cable connections
# Disable SATA power management in BIOS or via kernel param:
# GRUB_CMDLINE_LINUX="... libata.force=noncq"
sudo update-grub
```

---

## Tier 1 — Service Repair

### 9. zramswap Service Crash (lines 1301-1303)

```bash
# Fix zram compression algorithm
cat /proc/zswap/comp_algorithm
cat /sys/module/zram/parameters/compress_prio
# Install lz4 support
sudo apt install zstd zram-tools
# Configure zram
sudo nano /etc/default/zramswap
# Set: ZRAM_SWAP_COMPRESSION_ALGORITHM=lz4
# Or use zstd: ZRAM_SWAP_COMPRESSION_ALGORITHM=zstd
sudo systemctl restart zramswap
# Verify swap
swapon --show
cat /proc/swaps
# If zram not needed, disable it and use a regular swap file
sudo systemctl disable zramswap
sudo swapoff /dev/zram0
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 10. libvirtd Failure (lines 1340-1371)

```bash
# Create the missing CA certificate
sudo mkdir -p /etc/pki/CA
sudo openssl req -x509 -newkey rsa:4096 -keyout /etc/pki/CA/cakey.pem \
  -out /etc/pki/CA/cacert.pem -days 3650 -nodes -subj "/CN=libvirt-ca"
sudo chmod 600 /etc/pki/CA/cakey.pem
sudo chmod 644 /etc/pki/CA/cacert.pem
# Clear failed state and restart
sudo systemctl reset-failed libvirtd.service
sudo systemctl daemon-reload
sudo systemctl start libvirtd
# Verify
sudo virsh list --all
# If still failing, reinstall
sudo apt install libvirt-daemon-system libvirt-clients
sudo systemctl enable --now libvirtd
```

### 11. systemd-resolved DNS Collapse (lines 31.83-32.44)

```bash
# Fix DNS stub listener binding issue
sudo ss -tlnp | grep :53
# Option A: Configure resolved properly
sudo nano /etc/systemd/resolved.conf
#   [Resolve]
#   DNSStubListener=127.0.0.53
#   DNS=1.1.1.1 8.8.8.8
# Option B: Disable resolved, use dnsmasq
sudo systemctl stop systemd-resolved
sudo systemctl disable systemd-resolved
sudo apt install dnsmasq
sudo systemctl enable --now dnsmasq
# Option C: Ensure loopback interface is up
ip addr show lo
sudo ip link set lo up
sudo systemctl enable --now systemd-resolved
# Verify DNS
systemd-resolve --status
```

### 12. IRQ Balance Broken (lines 23.011-23.015)

```bash
# Check IRQ balance configuration
sudo cat /etc/default/irqbalance
# Fix the environment variable issue
sudo nano /etc/default/irqbalance
# Set: IRQBALANCE_ARGS="-o" (one_irq_per_core)
# Restart irqbalance
sudo systemctl restart irqbalance
ls /proc/irq/ | head
# If still failing, disable irqbalance and set affinity manually
sudo systemctl stop irqbalance
# Verify irqpoll is working (already in kernel cmdline)
cat /proc/cmdline | grep irqpoll
```

---

## Tier 2 — Security Lockdown Repair

### 13. Kernel Lockdown Restrictions (lines 80, 886, 1344, 1377-1378, 1443-1444)

```bash
# Check current lockdown state
cat /sys/kernel/security/lockdown
# Disable Secure Boot to lift most restrictions:
# Enter BIOS/UEFI setup (DEL), Security → Secure Boot → Disabled
# Or if Secure Boot must stay, enroll custom keys:
sudo mokutil --import /path/to/your/MOK.der
# Reboot and enroll MOK in firmware setup
# For Xorg raw I/O access:
sudo setcap cap_sys_rawio+ep /usr/bin/Xorg
# For hibernation:
# Disable Secure Boot entirely to unlock pm hibernate
```

### 14. IMA HTABLE Disabled (line 807)

```bash
# Enable IMA HTABLE for duplicate measurement recording
sudo nano /etc/default/grub
# Add to GRUB_CMDLINE_LINUX:
#   ima=on ima_hardware_update=1 IMA_APPRAISE=fix
sudo update-grub
# Configure IMA policy
sudo nano /etc/ima/ima-policy
# Add:
#   dont_measure fscache
#   measure func=BPRM_CHECK
# Rebuild initramfs
sudo update-initramfs -u -k all
# Verify IMA is working
cat /sys/kernel/security/ima/ascii-binary
```

### 15. TPM2 Services Skipped (lines 1085, 1117, 1119)

```bash
# Fix measured-uki condition
sudo apt install systemd-boot systemd-kmod
# Create unified kernel image
sudo ukify build --ukui=auto --output=/boot/vmlinuz-custom \
  --initrd=/boot/initrd.img-$(uname -r) \
  --cmdline="root=UUID=f394053c-e139-4dad-ae0b-922e09324d1e"
# Set up TPM2 PCR measurement
sudo systemctl enable systemd-pcrphase
sudo systemctl enable systemd-stub-resolve
# Re-enable skipped services
sudo systemctl reset-failed systemd-pcrmachine.service
sudo systemctl reset-failed systemd-tpm2-setup-early.service
sudo systemctl reset-failed systemd-pcrextend.socket
sudo systemctl daemon-reload
sudo systemctl enable --now systemd-pcrphase
sudo systemctl start systemd-tpm2-setup-early
```

### 16. debug-shell Service (line 1095)

```bash
# Disable the debug shell for security
sudo systemctl stop debug-shell
sudo systemctl disable debug-shell
sudo systemctl mask debug-shell.socket
# Verify it's disabled
sudo systemctl status debug-shell
# Remove any lingering symlinks
sudo rm -f /etc/systemd/system/getty.target.wants/debug-shell.service
```

---

## Tier 2 — System/Network/Driver Warnings

### 17. DRM Panic (lines 812, 1267)

```bash
# Reinstall GPU drivers and firmware
sudo apt install --reinstall xserver-xorg-video-amdgpu linux-firmware
sudo update-initramfs -u -k all
# If amdgpu panics, try modesetting with reduced features
sudo nano /etc/default/grub
# Add: amdgpu.dpm=0 amdgpu.ppfeaturemask=0x00000000
# or: amdgpu.dc=0 amdgpu.aspm=0
sudo update-grub
# Check for firmware issues
dmesg | grep -i "amdgpu.*fw\|firmware.*amdgpu" | tail -20
```

### 18. br_netfilter Missing (line 1373)

```bash
sudo modprobe br_netfilter
echo "br_netfilter" | sudo tee /etc/modules-load.d/br_netfilter.conf
lsmod | grep br_netfilter
sudo systemctl restart docker
```

### 19. Jack Audio RT Scheduling (lines 1364-1375)

```bash
sudo usermod -aG audio $USER
sudo usermod -aG pulse-access $USER
# Configure real-time scheduling limits
sudo nano /etc/security/limits.conf
# Add:
#   @audio    -  rtprio     95
#   @audio    -  memlock    unlimited
#   @audio    -  nice       -19
```

### 20. WirePlumber / PipeWire Issues (lines 1388-1433)

```bash
# Install missing libcamera SPA
sudo apt install libcamera-utils
# Install BlueZ
sudo apt install bluez
# Restart PipeWire
sudo systemctl restart pipewire pipewire-pulse wireplumber
```

### 21. Complete System Fix Script

```bash
#!/bin/bash
# Comprehensive repair script for dmesg anomalies

# 1. Fix firmware
sudo apt install --reinstall linux-firmware amd64-microcode

# 2. Fix zram
sudo apt install zstd zram-tools
sudo systemctl restart zramswap || true

# 3. Fix libvirtd
sudo mkdir -p /etc/pki/CA
sudo openssl req -x509 -newkey rsa:4096 -keyout /etc/pki/CA/cakey.pem \
  -out /etc/pki/CA/cacert.pem -days 3650 -nodes -subj "/CN=libvirt-ca"
sudo systemctl reset-failed libvirtd.service
sudo systemctl daemon-reload
sudo systemctl start libvirtd

# 4. Fix DNS
sudo apt install dnsmasq
sudo systemctl stop systemd-resolved
sudo systemctl disable systemd-resolved
sudo systemctl enable --now dnsmasq

# 5. Load missing kernel modules
sudo modprobe br_netfilter
echo "br_netfilter" | sudo tee /etc/modules-load.d/br_netfilter.conf

# 6. Disable security exposures
sudo systemctl stop debug-shell
sudo systemctl disable debug-shell
sudo systemctl mask debug-shell.socket

# 7. Fix IRQ balance
sudo systemctl restart irqbalance || true

# 8. Update grub with IOMMU fix
sudo nano /etc/default/grub
# Manually add: iommu=pt swiotlb=1
sudo update-grub

# 9. Rebuild initramfs
sudo update-initramfs -u -k all

# 10. Reboot
sudo reboot
```

### 22. BIOS/UEFI Settings to Verify

After applying software fixes, verify in BIOS/UEFI setup (DEL):

| Setting | Recommended Value |
|---------|-------------------|
| Secure Boot | DISABLE (or enroll custom keys) |
| AMD SVM Mode | ENABLE (for KVM) |
| IOMMU | ENABLE |
| CSM | DISABLE |
| TPM | ENABLE (fTPM or discrete) |
| Above 4G Decoding | ENABLE (for AMD-Vi) |
| USB XHCI Hand-off | ENABLE |
| SATA Mode | AHCI |
| Boot Protocol | UEFI |

Download latest firmware from: https://www.gigabyte.com/Motherboards/B450M-S2H-rev-1x#support

---

## Root Cause Summary

```
Broken BIOS/UEFI firmware
  → ACPI conflicts + CCP inaccessible
    → IOMMU cannot handle DMA properly
      → NVMe I/O page fault + SWIOTLB fallback
        → Device drivers fail (USB, SATA, zram)
          → Services crash (libvirtd, systemd-resolved, zramswap)
            → Lockdown restrictions compound the problem
              → System unstable and insecure
```

**Primary root cause: firmware/BIOS issues** (broken BIOS, ACPI table problems, missing AMD Secure Processor firmware) causing IOMMU/DMA remapping failures.

---

*Generated from analysis of /mnt/projects/fastapi/dmesg/dmesg.log (1480 lines)*
