This repository contains the implementation of a high-performance, multi-tenant hardware acceleration framework developed for the Xilinx Zynq UltraScale+ ZCU104 platform. The system integrates four domain-specific hardware accelerators with a specialized Resource-Aware Scheduler (RAS) to enable safe, concurrent task offloading from edge devices and microcontrollers.

Overview

Modern edge devices face a "Communication Wall" where the benefits of hardware acceleration are often bottlenecked by software and network overhead. This project addresses these challenges by:Decoupled Parallel Execution: Utilizing a distributed switch fabric with five independent SmartConnect IPs to isolate control and data traffic.Multi-Tenancy: Implementing a mutex-based reservation table to manage concurrent Flask-based requests without AXI-bus contention.Fault Tolerance: A soft-reset protocol to recover stalled DMA channels without requiring an OS reboot.🛠 Hardware ArchitectureThe design is implemented on the Zynq UltraScale+ MPSoC. It features a tiered AXI interconnect strategy to prevent Head-of-Line (HoL) blocking and ensure deterministic latency.

Accelerator,Implementation Detail,Functionality
Non-Linear Activation (ReLU),Vitis HLS Pipeline ,High-throughput streaming of 32-bit floating-point data.
Cryptographic XOR,Logic-gate-level engine ,Lightweight bitwise stream cipher with a 32-bit key.
Greyscale Image Filter,Parallel Luminosity Algorithm ,"Simultaneous processing of R, G, and B channels for RGBA formats."
Matrix Processing Unit,Systolic-array inspired ,High-speed MAC operations using 32 DSP48E2 slices.

Accelerator,Implementation Detail,Functionality
Non-Linear Activation (ReLU),Vitis HLS Pipeline ,High-throughput streaming of 32-bit floating-point data.
Cryptographic XOR,Logic-gate-level engine ,Lightweight bitwise stream cipher with a 32-bit key.
Greyscale Image Filter,Parallel Luminosity Algorithm ,"Simultaneous processing of R, G, and B channels for RGBA formats."
Matrix Processing Unit,Systolic-array inspired ,High-speed MAC operations using 32 DSP48E2 slices.

├── ips/                        # Vitis HLS and RTL source files for accelerators
│   ├── relu/                   # Activation Kernel source code
│   ├── crypto/                 # XOR Engine source code
│   ├── image_filter/           # Greyscale Filter source code
│   └── matrix_mult/            # Systolic Array multiplier source code
├── middleware/                 # Flask server and RAS implementation
├── bitstream/                  # Compiled .bit and .hwh files for ZCU104
└── README.md
