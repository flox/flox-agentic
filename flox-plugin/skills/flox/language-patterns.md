# Language-Specific Development Patterns

## Python and Python Virtual Environments

### venv Creation Pattern
Always check existence before activation - `uv venv` may not complete synchronously:
```bash
if [ ! -d "$venv" ]; then
  uv venv "$venv" --python python3
fi
# Guard activation - venv creation might not be complete
if [ -f "$venv/bin/activate" ]; then
  source "$venv/bin/activate"
fi
```

### Key Python Patterns
- **venv location**: Always use `$FLOX_ENV_CACHE/venv` - survives environment rebuilds
- **uv with venv**: Use `uv pip install --python "$venv/bin/python"` NOT `"$venv/bin/python" -m uv`
- **Service commands**: Use venv Python directly: `$FLOX_ENV_CACHE/venv/bin/python` not `python`
- **Activation**: Always `source "$venv/bin/activate"` before pip/uv operations
- **PyTorch CUDA**: Install with `--index-url https://download.pytorch.org/whl/cu124` for GPU support
- **PyTorch gotcha**: Needs `gcc-unwrapped` for libstdc++.so.6, not just `gcc`
- **PyTorch CPU/GPU**: Use separate index URLs: `/whl/cpu` vs `/whl/cu124` (don't mix!)
- **Service scripts**: Must activate venv inside service command, not rely on hook activation
- **Cache dirs**: Set `UV_CACHE_DIR` and `PIP_CACHE_DIR` to `$FLOX_ENV_CACHE` subdirs
- **Dependency installation flag**: Touch `$FLOX_ENV_CACHE/.deps_installed` to prevent reinstalls

### Service venv Pattern
Always use absolute paths and explicit activation in service commands:
```toml
[services.myapp]
command = '''
source "$FLOX_ENV_CACHE/venv/bin/activate"
exec "$FLOX_ENV_CACHE/venv/bin/python" app.py
'''
```

### Using Python Packages from Catalog
Override data dirs to use local paths:
```toml
[install]
myapp.pkg-path = "owner/myapp"
[vars]
MYAPP_DATA = "$FLOX_ENV_PROJECT"  # Use repo not ~/.myapp
```

### Wrapping Package Commands
Alias to customize behavior:
```bash
# In [profile]
alias myapp-setup="MYAPP_DATA=$FLOX_ENV_PROJECT command myapp-setup"
```

**Note**: `uv` is installed in the Flox environment, not inside the venv. We use `uv pip install --python "$venv/bin/python"` so that `uv` targets the venv's Python interpreter.

## C/C++ Development Environments

### Key Patterns
- **Package Names**: `gbenchmark` not `benchmark`, `catch2_3` for Catch2, `gcc13`/`clang_18` for specific versions
- **System Constraints**: Linux-only tools need explicit systems: `valgrind.systems = ["x86_64-linux", "aarch64-linux"]`
- **Essential Groups**: Separate `compilers`, `build`, `debug`, `testing`, `libraries` groups prevent conflicts
- **Core Stack**: gcc13/clang_18, cmake/ninja/make, gdb/lldb, boost/eigen/fmt/spdlog, gtest/catch2/gbenchmark

### libstdc++ Access
ALWAYS include `gcc-unwrapped` for C++ stdlib headers/libs (gcc alone doesn't expose them):
```toml
gcc-unwrapped.pkg-path = "gcc-unwrapped"
gcc-unwrapped.priority = 5  # Lower priority to avoid conflicts
gcc-unwrapped.pkg-group = "libraries"
```

## Node.js Development Environments

### Key Patterns
- **Package managers**: Install `nodejs` (includes npm); add `yarn` or `pnpm` separately if needed
- **Version pinning**: Use `version = "^20.0"` for LTS, or exact versions for reproducibility
- **Global tools pattern**: Use `npx` for one-off tools, install commonly-used globals in manifest

### Service Pattern
Always specify host/port for network services:
```toml
[services.dev-server]
command = '''exec npm run dev -- --host "$DEV_HOST" --port "$DEV_PORT"'''
```

## CUDA Development Environments

### Prerequisites & Authentication
- Sign up for early access at https://flox.dev, authenticate with `flox auth login`
- **Linux-only**: CUDA packages only work on `["aarch64-linux", "x86_64-linux"]`
- All CUDA packages are prefixed with `flox-cuda/` in the catalog

### Package Discovery
```bash
flox search cudatoolkit --all | grep flox-cuda
flox search nvcc --all | grep 12_8              # Specific versions
flox show flox-cuda/cudaPackages.cudatoolkit    # All available versions
```

### Essential CUDA Packages
| Package Pattern | Purpose | Example |
|-----------------|---------|---------|
| `cudaPackages_X_Y.cudatoolkit` | Main CUDA Toolkit | `cudaPackages_12_8.cudatoolkit` |
| `cudaPackages_X_Y.cuda_nvcc` | NVIDIA C++ Compiler | `cudaPackages_12_8.cuda_nvcc` |
| `cudaPackages.cuda_cudart` | CUDA Runtime API | `cuda_cudart` |
| `cudaPackages_X_Y.libcublas` | Linear algebra | `cudaPackages_12_8.libcublas` |
| `cudaPackages_X_Y.cudnn_9_11` | Deep neural networks | `cudaPackages_12_8.cudnn_9_11` |

### Critical: Conflict Resolution
**CUDA packages have LICENSE file conflicts requiring explicit priorities:**
```toml
[install]
cuda_nvcc.pkg-path = "flox-cuda/cudaPackages_12_8.cuda_nvcc"
cuda_nvcc.systems = ["aarch64-linux", "x86_64-linux"]
cuda_nvcc.priority = 1                    # Highest priority

cuda_cudart.pkg-path = "flox-cuda/cudaPackages.cuda_cudart"
cuda_cudart.systems = ["aarch64-linux", "x86_64-linux"]
cuda_cudart.priority = 2

cudatoolkit.pkg-path = "flox-cuda/cudaPackages_12_8.cudatoolkit"
cudatoolkit.systems = ["aarch64-linux", "x86_64-linux"]
cudatoolkit.priority = 3                  # Lower for LICENSE conflicts

gcc.pkg-path = "gcc"
gcc-unwrapped.pkg-path = "gcc-unwrapped"  # For libstdc++
gcc-unwrapped.priority = 5
```

### Cross-Platform GPU Development
Dual CUDA/CPU packages for portability (Linux gets CUDA, macOS gets CPU fallback):
```toml
[install]
## CUDA packages (Linux only)
cuda-pytorch.pkg-path = "flox-cuda/python3Packages.torch"
cuda-pytorch.systems = ["x86_64-linux", "aarch64-linux"]
cuda-pytorch.priority = 1

## Non-CUDA packages (macOS + Linux fallback)
pytorch.pkg-path = "python313Packages.pytorch"
pytorch.systems = ["x86_64-darwin", "aarch64-darwin"]
pytorch.priority = 6                     # Lower priority
```

### GPU Detection Pattern
**Dynamic CPU/GPU package installation in hooks:**
```bash
setup_gpu_packages() {
  venv="$FLOX_ENV_CACHE/venv"

  if [ ! -f "$FLOX_ENV_CACHE/.deps_installed" ]; then
    if lspci 2>/dev/null | grep -E 'NVIDIA|AMD' > /dev/null; then
      echo "GPU detected, installing CUDA packages"
      uv pip install --python "$venv/bin/python" \
        torch torchvision --index-url https://download.pytorch.org/whl/cu129
    else
      echo "No GPU detected, installing CPU packages"
      uv pip install --python "$venv/bin/python" \
        torch torchvision --index-url https://download.pytorch.org/whl/cpu
    fi
    touch "$FLOX_ENV_CACHE/.deps_installed"
  fi
}
```

### Best Practices
- **Always use priority values**: CUDA packages have predictable conflicts
- **Version consistency**: Use specific versions (e.g., `_12_8`) for reproducibility
- **Modular design**: Split base CUDA, math libs, debugging into separate environments
- **Test compilation**: Verify `nvcc hello.cu -o hello` works after setup
- **Platform constraints**: Always include `systems = ["aarch64-linux", "x86_64-linux"]`

### Common CUDA Gotchas
- **CUDA toolkit ≠ complete toolkit**: Add libraries (libcublas, cudnn) as needed
- **License conflicts**: Every CUDA package may need explicit priority
- **No macOS support**: Use Metal alternatives on Darwin
- **Version mixing**: Don't mix CUDA versions; use consistent `_X_Y` suffixes

### Complete CUDA Example
```toml
[install]
cuda_nvcc.pkg-path = "flox-cuda/cudaPackages_12_8.cuda_nvcc"
cuda_nvcc.priority = 1
cuda_cudart.pkg-path = "flox-cuda/cudaPackages.cuda_cudart"
cuda_cudart.priority = 2
libcublas.pkg-path = "flox-cuda/cudaPackages.libcublas"
torch.pkg-path = "flox-cuda/python3Packages.torch"
python313Full.pkg-path = "python313Full"
uv.pkg-path = "uv"
gcc.pkg-path = "gcc"
gcc-unwrapped.pkg-path = "gcc-unwrapped"
gcc-unwrapped.priority = 5

[vars]
CUDA_VERSION = "12.8"
PYTORCH_CUDA_ALLOC_CONF = "max_split_size_mb:128"

[hook]
setup_cuda_venv() {
  venv="$FLOX_ENV_CACHE/venv"
  [ ! -d "$venv" ] && uv venv "$venv" --python python3
  [ -f "$venv/bin/activate" ] && source "$venv/bin/activate"
}
```

## Platform-Specific Patterns

### Darwin-Specific Frameworks and Tools
```toml
# Darwin-specific frameworks
IOKit.pkg-path = "darwin.apple_sdk.frameworks.IOKit"
IOKit.systems = ["x86_64-darwin", "aarch64-darwin"]
CoreFoundation.pkg-path = "darwin.apple_sdk.frameworks.CoreFoundation"
CoreFoundation.priority = 2
CoreFoundation.systems = ["x86_64-darwin", "aarch64-darwin"]

# Platform-preferred compilers (remove constraints if cross-platform needed)
gcc.pkg-path = "gcc"
gcc.systems = ["x86_64-linux", "aarch64-linux"]
clang.pkg-path = "clang"
clang.systems = ["x86_64-darwin", "aarch64-darwin"]

# Darwin GNU compatibility layer (Darwin's built-ins are ancient/limited)
coreutils.pkg-path = "coreutils"
coreutils.systems = ["x86_64-darwin", "aarch64-darwin"]
gnumake.pkg-path = "gnumake"
gnumake.systems = ["x86_64-darwin", "aarch64-darwin"]
gnused.pkg-path = "gnused"
gnused.systems = ["x86_64-darwin", "aarch64-darwin"]
gawk.pkg-path = "gawk"
gawk.systems = ["x86_64-darwin", "aarch64-darwin"]
bashInteractive.pkg-path = "bashInteractive"
bashInteractive.systems = ["x86_64-darwin", "aarch64-darwin"]
```

**Note**: CUDA is Linux-only; use Metal-accelerated packages on Darwin when available.
